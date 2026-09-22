"""Build the model/*.pkl artifacts (movie list + similarity matrix).

Run once:  python build_model.py
"""

import os
import pickle

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(HERE, "model")


def build():
    os.makedirs(MODEL_DIR, exist_ok=True)

    source = os.path.join(HERE, "moive.pkl")
    if not os.path.exists(source):
        raise FileNotFoundError(f"Missing source file: {source}")

    print(f"Loading {source}...")
    movies = pd.read_pickle(source)
    movies["tags"] = movies["tags"].fillna("").astype(str)

    print("Vectorizing movie tags (CountVectorizer max_features=5000)...")
    vectorizer = CountVectorizer(max_features=5000, stop_words="english")
    vectors = vectorizer.fit_transform(movies["tags"]).toarray()

    print("Computing cosine similarity matrix...")
    similarity = cosine_similarity(vectors).astype(np.float32)

    movie_list_dest = os.path.join(MODEL_DIR, "movie_list.pkl")
    similarity_dest = os.path.join(MODEL_DIR, "similarity.pkl")

    movies.to_pickle(movie_list_dest)
    with open(similarity_dest, "wb") as fh:
        pickle.dump(similarity, fh, protocol=pickle.HIGHEST_PROTOCOL)

    print("Build complete.")
    print(f"  movies:           {movies.shape}")
    print(f"  similarity:       {similarity.shape} (float32, {similarity.nbytes / (1024*1024):.1f} MB)")
    print(f"  output directory: {MODEL_DIR}")


if __name__ == "__main__":
    build()
