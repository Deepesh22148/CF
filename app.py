from flask import Flask, request, jsonify
from flask_cors import CORS
from data_loader import load_data, get_user_history, get_movie_info, get_user_info
from prompts import generate_prompt, generate_batch_prompt
from llm_client import get_rating_from_llm, get_batch_ratings_from_llm
from hybrid_recommender import HybridRecommender
import os

app = Flask(__name__, static_folder='frontend', static_url_path='/')
CORS(app)

print("Loading data for server...")
items, users, train_ratings, test_ratings = load_data("ml-100k")
print("Init SVD Hybrid Recommender for serving...")
hybrid_rec = HybridRecommender(n_components=50)
hybrid_rec.fit(train_ratings)
print("Data and Model loaded perfectly.")

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/recommend', methods=['POST'])
def recommend():
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
        
    try:
        user_id = int(user_id)
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
        
        return jsonify({
            "user_info": {
                "age": int(age),
                "gender": str(gender),
                "occupation": str(occupation),
                "liked_samples": [str(x) for x in high_rated[:3]]
            },
            "recommendations": top_5,
            "rate_limited": used_fallback
        })
    except Exception as e:
        print(f"Error during recommendation: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
