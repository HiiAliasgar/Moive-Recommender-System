"""Build the model/*.pkl artifacts (movie list + similarity matrix).

Run once:  python build_model.py
"""

import os
import pickle

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

    movies = pd.read_pickle(source)
    movies["tags"] = movies["tags"].fillna("").astype(str)

    vectorizer = CountVectorizer(max_features=5000, stop_words="english")
    vectors = vectorizer.fit_transform(movies["tags"]).toarray()
    similarity = cosine_similarity(vectors)

    movies.to_pickle(os.path.join(MODEL_DIR, "movie_list.pkl"))
    with open(os.path.join(MODEL_DIR, "similarity.pkl"), "wb") as fh:
        pickle.dump(similarity, fh)

    print(f"Build complete.")
    print(f"  movies:           {movies.shape}")
    print(f"  similarity:       {similarity.shape}")
    print(f"  output directory: {MODEL_DIR}")


if __name__ == "__main__":
    build()
