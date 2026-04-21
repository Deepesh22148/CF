import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from sklearn.decomposition import TruncatedSVD

class HybridRecommender:
    def __init__(self, n_components=50):
        self.n_components = n_components
        self.svd = TruncatedSVD(n_components=self.n_components, random_state=42)
        self.user_map = {}
        self.item_map = {}
        self.user_inv_map = {}
        self.item_inv_map = {}
        self.user_factors = None
        self.item_factors = None
        
    def fit(self, train_ratings):
        # Create mappings for contiguous integer indices
        unique_users = train_ratings['user_id'].unique()
        unique_items = train_ratings['movie_id'].unique()
        
        self.user_map = {u: i for i, u in enumerate(unique_users)}
        self.user_inv_map = {i: u for i, u in enumerate(unique_users)}
        
        self.item_map = {item: i for i, item in enumerate(unique_items)}
        self.item_inv_map = {i: item for i, item in enumerate(unique_items)}
        
        # Map IDs to indices
        row = train_ratings['user_id'].map(self.user_map).values
        col = train_ratings['movie_id'].map(self.item_map).values
        data = train_ratings['rating'].values
        
        # Build Sparse User-Item Matrix
        num_users = len(unique_users)
        num_items = len(unique_items)
        sparse_matrix = coo_matrix((data, (row, col)), shape=(num_users, num_items)).tocsr()
        
        # Fit SVD
        self.user_factors = self.svd.fit_transform(sparse_matrix)
        self.item_factors = self.svd.components_.T  # shape: (num_items, n_components)
        
    def get_top_k_candidates(self, user_id, batch_items, k=20):
        """
        Scores the batch_items for the given user, returns the top_k candidates to send to the LLM.
        Also returns a dict of SVD scores for all batch items (to be used as fallback).
        """
        if user_id not in self.user_map:
            # Cold start user, fallback to returning first K
            return batch_items[:k], {item: 0.0 for item in batch_items}
            
        u_idx = self.user_map[user_id]
        u_vec = self.user_factors[u_idx]
        
        scores = {}
        for item in batch_items:
            if item in self.item_map:
                i_idx = self.item_map[item]
                i_vec = self.item_factors[i_idx]
                score = np.dot(u_vec, i_vec)
            else:
                score = 0.0  # Cold start item
            scores[item] = score
            
        # Sort items by SVD score
        ranked_items = sorted(batch_items, key=lambda x: scores[x], reverse=True)
        top_k = ranked_items[:k]
        
        return top_k, scores
