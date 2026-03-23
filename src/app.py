import os
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import cosine

class MusicRecommender:
    def __init__(self, data_path):
        self.data = pd.read_csv(data_path)
        self.user_item_matrix = self.data.pivot_table(index='user_id', columns='track_id', values='rating')
        self.user_item_matrix = self.user_item_matrix.fillna(0)

    def get_user_recommendations(self, user_id, top_n=10):
        user_preferences = self.user_item_matrix.loc[user_id]
        item_similarities = self.user_item_matrix.T.corrwith(user_preferences)
        item_similarities = item_similarities.sort_values(ascending=False)
        recommended_items = item_similarities.head(top_n).index.tolist()
        return recommended_items

    def get_similar_users(self, user_id, top_n=10):
        user_preferences = self.user_item_matrix.loc[user_id]
        user_similarities = self.user_item_matrix.corrwith(user_preferences)
        user_similarities = user_similarities.sort_values(ascending=False)
        similar_users = user_similarities.head(top_n+1).drop(user_id).index.tolist()
        return similar_users

    def get_personalized_recommendations(self, user_id, top_n=10):
        similar_users = self.get_similar_users(user_id)
        user_recommendations = []
        for similar_user in similar_users:
            user_recommendations.extend(self.get_user_recommendations(similar_user))
        unique_recommendations = list(set(user_recommendations))
        return unique_recommendations[:top_n]
