import json
import os
import sys

# Add parent CF_Project directory to path to reuse the ML files from the original project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

from data_loader import load_data, get_user_history, get_movie_info, get_user_info
from prompts import generate_batch_prompt
from llm_client import get_batch_ratings_from_llm
from hybrid_recommender import HybridRecommender

print("Loading data for server...")
# Retrieve the correct ml-100k data path
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..', 'ml-100k'))
items, users, train_ratings, test_ratings = load_data(data_dir)

print("Init SVD Hybrid Recommender for serving...")
hybrid_rec = HybridRecommender(n_components=50)
hybrid_rec.fit(train_ratings)
print("Data and Model loaded perfectly.")

async def get_recommendation(body : str):
    
    body = json.loads(body)
    mode = body.get("mode")
    user_id = body.get("user_id")
    
    if mode == "dataset":
        # dataset mode
        return await get_recommendation_dataset_mode(user_id)
    else:
        # personel mode
        return await get_recommendation_personel_mode()
        
# Cache dictionary to prevent spamming the LLM API on exactly same requests
recommendation_cache = {}

async def get_recommendation_dataset_mode(user_id):
    if not user_id:
        return {"error": "user_id is required"}
        
    try:
        user_id = int(user_id)
        
        # 1. Return immediately from cache if this user has already been calculated to dodge API Rate limits
        if user_id in recommendation_cache:
            print(f"Returning cached recommendations for user {user_id}")
            return recommendation_cache[user_id]
            
        age, gender, occupation = get_user_info(user_id, users)
        high_rated, low_rated = get_user_history(user_id, train_ratings, items)
        
        hit_items = train_ratings[train_ratings['user_id'] == user_id]['movie_id'].unique()
        available_items = items[~items['movie_id'].isin(hit_items)]['movie_id'].tolist()
        
        # Use SVD to get top 15 candidates instead of random sampling
        top_candidates_ids, svd_scores = hybrid_rec.get_top_k_candidates(user_id, available_items, k=15)
        
        recommendations = []
        target_movies = []
        for movie_id in top_candidates_ids:
            target_title, target_year, target_genres = get_movie_info(movie_id, items)
            target_movies.append({
                "movie_id": movie_id,
                "title": target_title,
                "year": target_year,
                "genres": target_genres
            })
            
        prompt = generate_batch_prompt(
            age=int(age),
            gender=str(gender),
            occupation=str(occupation),
            high_rated_movies=high_rated,
            low_rated_movies=low_rated,
            target_movies=target_movies
        )
        
        scores = get_batch_ratings_from_llm(prompt, len(target_movies))
        
        # Handle Rate limits: if all scores came back as exactly 50, use SVD scores to rank them gracefully
        used_fallback = all(s == 50 for s in scores)
        
        for idx, target_movie in enumerate(target_movies):
            s_id = target_movie["movie_id"]
            if used_fallback:
                # If API rate limited, scale SVD dot product roughly to 0-100 logic for UI purposes
                base_score = min(max(int(svd_scores[s_id] * 20 + 30), 0), 100)
            else:
                base_score = int(scores[idx])
                
            recommendations.append({
                "movie_id": int(s_id),
                "title": str(target_movie["title"]),
                "genres": str(target_movie["genres"]),
                "score": base_score
            })
            
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        # Select top 5 to display
        top_5 = recommendations[:5]
        
        result_payload = {
            "user_info": {
                "age": int(age),
                "gender": str(gender),
                "occupation": str(occupation),
                "liked_samples": [str(x) for x in high_rated[:3]]
            },
            "recommendations": top_5,
            "rate_limited": used_fallback
        }
        
        # 2. Store to cache so the next lookup avoids LLM rate limits entirely if the user clicks again
        recommendation_cache[user_id] = result_payload
        
        return result_payload
    except Exception as e:
        print(f"Error during recommendation: {e}")
        return {"error": str(e)}

async def get_recommendation_personel_mode():
    return None