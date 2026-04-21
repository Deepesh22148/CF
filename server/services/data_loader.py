import pandas as pd
import os
import numpy as np

def load_data(data_dir="ml-100k"):
    # Load items (movies)
    item_cols = ['movie_id', 'title', 'release_date', 'video_release_date', 'imdb_url', 
                 'unknown', 'Action', 'Adventure', 'Animation', 'Childrens', 'Comedy', 
                 'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 
                 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western']
    items_path = os.path.join(data_dir, 'u.item')
    items = pd.read_csv(items_path, sep='|', names=item_cols, encoding='latin-1', usecols=['movie_id', 'title', 'release_date', 'Action', 'Adventure', 'Animation', 'Childrens', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western'])
    
    # Load users
    user_cols = ['user_id', 'age', 'gender', 'occupation', 'zip_code']
    users_path = os.path.join(data_dir, 'u.user')
    users = pd.read_csv(users_path, sep='|', names=user_cols, encoding='latin-1')
    
    # Load training ratings
    rating_cols = ['user_id', 'movie_id', 'rating', 'timestamp']
    train_path = os.path.join(data_dir, 'u1.base')
    train_ratings = pd.read_csv(train_path, sep='\t', names=rating_cols)
    
    # Load test ratings
    test_path = os.path.join(data_dir, 'u1.test')
    test_ratings = pd.read_csv(test_path, sep='\t', names=rating_cols)
    
    return items, users, train_ratings, test_ratings

def get_user_history(user_id, train_ratings, items):
    user_ratings = train_ratings[train_ratings['user_id'] == user_id]
    
    # Merge with items to get titles
    user_ratings = pd.merge(user_ratings, items[['movie_id', 'title']], on='movie_id')
    
    # Define highly rated and poorly rated
    high_rated = user_ratings[user_ratings['rating'] >= 4]['title'].tolist()
    low_rated = user_ratings[user_ratings['rating'] <= 2]['title'].tolist()
    
    # Take a sample to avoid context window explosion (e.g. top 10 movies highly rated)
    high_rated_sample = high_rated[:15] if len(high_rated) > 15 else high_rated
    low_rated_sample = low_rated[:10] if len(low_rated) > 10 else low_rated
    
    return high_rated_sample, low_rated_sample

def get_movie_info(movie_id, items):
    movie = items[items['movie_id'] == movie_id].iloc[0]
    title = movie['title']
    
    # Extract year
    release_date_str = str(movie.get('release_date', ''))
    year = release_date_str[-4:] if len(release_date_str) >= 4 and release_date_str[-4:].isdigit() else "Unknown"
    
    # Extract genres
    genres = []
    genre_cols = ['Action', 'Adventure', 'Animation', 'Childrens', 'Comedy', 
                  'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 
                  'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western']
    for g in genre_cols:
        if movie[g] == 1:
            genres.append(g)
            
    genre_str = ", ".join(genres)
    return title, year, genre_str

def get_user_info(user_id, users):
    user = users[users['user_id'] == user_id].iloc[0]
    return user['age'], user['gender'], user['occupation']

def get_leave_one_out_batch(user_id, train_ratings, test_ratings, items, num_negatives=99):
    # Items user interacted with in train
    hit_items = train_ratings[train_ratings['user_id'] == user_id]['movie_id'].unique()
    
    # Get positive test items (binarized: rating >= 4 is a hit)
    user_test_ratings = test_ratings[(test_ratings['user_id'] == user_id) & (test_ratings['rating'] >= 4)]
    if len(user_test_ratings) == 0:
        return None, None
        
    # Sample 1 positive test item
    target_item = user_test_ratings.sample(1, random_state=42).iloc[0]['movie_id']
    
    # Get negative items (items not in train and not the target item)
    all_items = items['movie_id'].unique()
    available_negatives = np.setdiff1d(all_items, np.append(hit_items, [target_item]))
    
    if len(available_negatives) < num_negatives:
        negatives = available_negatives
    else:
        np.random.seed(user_id) # Deterministic for user
        negatives = np.random.choice(available_negatives, size=num_negatives, replace=False)
        
    batch_items = [target_item] + list(negatives)
    labels = [1] + [0] * len(negatives)
    
    return batch_items, labels
