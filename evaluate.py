import argparse
import pandas as pd
import numpy as np
import asyncio
from tqdm.asyncio import tqdm
from sklearn.metrics import ndcg_score
from data_loader import load_data, get_user_history, get_movie_info, get_user_info, get_leave_one_out_batch
from prompts import generate_batch_prompt
from llm_client import get_batch_ratings_from_llm_async
from hybrid_recommender import HybridRecommender

def get_hit_rate(ranked_list, target_item, k=10):
    return int(target_item in ranked_list[:k])

async def evaluate_user_async(user_id, train_ratings, test_ratings, items, users, hybrid_rec, args, sem):
    async with sem:
        batch_items, labels = get_leave_one_out_batch(user_id, train_ratings, test_ratings, items, num_negatives=99)
        if batch_items is None:
            return None
            
        target_item = batch_items[0]
        
        try:
            # 1. Gather user info
            age, gender, occupation = get_user_info(user_id, users)
            high_rated, low_rated = get_user_history(user_id, train_ratings, items)
            
            # 2. Pre-filter candidates using Hybrid SVD
            top_k_candidates, svd_scores = hybrid_rec.get_top_k_candidates(user_id, batch_items, k=25)
            
            target_movies = []
            for movie_id in top_k_candidates:
                target_title, target_year, target_genres = get_movie_info(movie_id, items)
                target_movies.append({
                    "movie_id": movie_id,
                    "title": target_title,
                    "year": target_year,
                    "genres": target_genres
                })
            
            # 3. Generate Batch Prompt for top candidates
            prompt = generate_batch_prompt(
                age=age,
                gender=gender,
                occupation=occupation,
                high_rated_movies=high_rated,
                low_rated_movies=low_rated,
                target_movies=target_movies
            )
            
            # 4. LLM Prediction
            predictions = await get_batch_ratings_from_llm_async(prompt, len(target_movies))
                
            # 5. Evaluate for user
            final_scores = []
            for item in batch_items:
                if item in top_k_candidates:
                    idx = top_k_candidates.index(item)
                    # Score is strictly positive, 0-100
                    final_scores.append(predictions[idx])
                else:
                    # Give it a lower score based on SVD rank
                    final_scores.append(-10 + svd_scores[item])
            
            item_scores = list(zip(batch_items, final_scores))
            item_scores.sort(key=lambda x: x[1], reverse=True)
            ranked_items = [x[0] for x in item_scores]
            
            hr = get_hit_rate(ranked_items, target_item, k=args.k)
            ndcg = ndcg_score([labels], [final_scores], k=args.k)
            
            return {
                'user_id': user_id,
                'target_item': target_item,
                'hit_rate': hr,
                'ndcg': ndcg
            }
        except Exception as e:
            print(f"Error evaluating user {user_id}: {e}")
            return None

async def main_async():
    parser = argparse.ArgumentParser(description="Evaluate LLM Ratings on MovieLens 100K")
    parser.add_argument("--data_dir", type=str, default="ml-100k", help="Path to MovieLens 100K dir")
    parser.add_argument("--subset", type=int, default=10, help="Number of users to evaluate (Leave-One-Out)")
    parser.add_argument("--k", type=int, default=10, help="K for HR@K and NDCG@K")
    parser.add_argument("--output", type=str, default="predictions.csv", help="Output CSV file")
    args = parser.parse_args()

    print("Loading data...")
    items, users, train_ratings, test_ratings = load_data(args.data_dir)
    print(f"Loaded {len(train_ratings)} training ratings and {len(test_ratings)} test ratings.")
    
    unique_users = test_ratings['user_id'].unique()
    if args.subset > 0 and args.subset < len(unique_users):
        np.random.seed(42)
        eval_users = np.random.choice(unique_users, size=args.subset, replace=False)
    else:
        eval_users = unique_users

    print("Init SVD Hybrid Recommender for candidate generation...")
    hybrid_rec = HybridRecommender(n_components=50)
    hybrid_rec.fit(train_ratings)
    
    print(f"Evaluating {len(eval_users)} users asynchronously with Leave-One-Out approach...")

    # Limit concurrency to 5 so we don't trigger Free Tier rate limits instantly
    sem = asyncio.Semaphore(5)
    tasks = [evaluate_user_async(u, train_ratings, test_ratings, items, users, hybrid_rec, args, sem) for u in eval_users]
    
    results = await tqdm.gather(*tasks)
    results_list = [r for r in results if r is not None]

    if not results_list:
        print("No valid evaluation batches found.")
        return

    hit_rates = [r['hit_rate'] for r in results_list]
    ndcgs = [r['ndcg'] for r in results_list]

    print(f"\n--- Final Results metrics computed over {len(results_list)} users ---")
    print(f"HR@{args.k}: {np.mean(hit_rates):.4f}")
    print(f"NDCG@{args.k}: {np.mean(ndcgs):.4f}")
    
    # 6. Save results
    results_df = pd.DataFrame(results_list)
    results_df.to_csv(args.output, index=False)
    print(f"Saved predictions to {args.output}")

if __name__ == "__main__":
    asyncio.run(main_async())
