"""Professional movie recommendation engine.

Content-based recommendation built on the movie tag (description + keyword)
vectors, loaded from the pre-computed cosine similarity matrix.
"""

import os
import pickle
import random

import pandas as pd

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model")


def load_data():
    """Load the movie list and similarity matrix."""
    movie_list_path = os.path.join(MODEL_DIR, "movie_list.pkl")
    similarity_path = os.path.join(MODEL_DIR, "similarity.pkl")

    if not os.path.exists(movie_list_path):
        movie_list_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "moive.pkl"
        )

    movies = pd.read_pickle(movie_list_path)
    if not os.path.exists(similarity_path):
        raise FileNotFoundError(
            "model/similarity.pkl is missing. "
            "Run `python build_model.py` to generate the model artifacts."
        )
    with open(similarity_path, "rb") as fh:
        similarity = pickle.load(fh)
    return movies, similarity


GENRE_ALIAS = {
    "sciencefict": "sci-fi",
    "scifi": "sci-fi",
    "mysteri": "mystery",
    "romanc": "romance",
    "adventur": "adventure",
    "action": "action",
    "adventure": "adventure",
    "animation": "animation",
    "comedy": "comedy",
    "crime": "crime",
    "drama": "drama",
    "fantasi": "fantasy",
    "fantasy": "fantasy",
    "horror": "horror",
    "thriller": "thriller",
    "sport": "sport",
}


def extract_genres(tags):
    """Extract a set of human readable genres from a raw tag string."""
    if not isinstance(tags, str):
        return []
    tags_lower = tags.lower()
    genres = set()
    for alias, genre in GENRE_ALIAS.items():
        if alias in tags_lower:
            genres.add(genre)
    return sorted(genres)


class Recommender:
    """Encapsulates all recommendation strategies and metadata helpers."""

    def __init__(self, movies, similarity):
        self.movies = movies
        self.similarity = similarity
        self.titles = movies["title"].tolist()
        self._genre_cache = {}

    # ----- metadata helpers -----
    def genres_of(self, title):
        if title not in self._genre_cache:
            tags = self.movies.loc[
                self.movies["title"] == title, "tags"
            ].values
            tags = tags[0] if len(tags) else ""
            self._genre_cache[title] = extract_genres(tags)
        return self._genre_cache[title]

    def tags_of(self, title):
        row = self.movies[self.movies["title"] == title]
        if row.empty:
            return ""
        return row.iloc[0]["tags"]

    def movie_id_of(self, title):
        row = self.movies[self.movies["title"] == title]
        return row.iloc[0]["movie_id"] if not row.empty else None

    def search(self, query, limit=20):
        """Case/space-insensitive title search."""
        query = query.strip().lower()
        if not query:
            return []
        matches = [
            t for t in self.titles
            if query in t.lower()
        ]
        return sorted(matches, key=lambda t: (not t.lower().startswith(query), len(t)))[:limit]

    # ----- strategies -----
    def by_similarity(self, movie, n=5):
        """Content-based similar movies, excluding the selected one."""
        matches = self.movies.index[
            self.movies["title"] == movie
        ]
        if matches.empty:
            return []
        index = matches[0]
        scored = sorted(
            list(enumerate(self.similarity[index])),
            key=lambda x: x[1],
            reverse=True,
        )
        results = []
        for idx, score in scored:
            if idx == index:
                continue
            results.append(
                {
                    "title": self.movies.iloc[idx]["title"],
                    "score": round(float(score), 3),
                    "id": self.movies.iloc[idx]["movie_id"],
                }
            )
            if len(results) >= n:
                break
        return results

    def by_genre(self, genre, n=10):
        """Recommend random-but-relevant movies within a chosen genre."""
        genre_movies = [
            title for title in self.titles
            if genre in self.genres_of(title)
        ]
        random.shuffle(genre_movies)
        return [
            {"title": t, "score": None, "id": self.movie_id_of(t)}
            for t in genre_movies[:n]
        ]

    def by_genre_similar(self, movie, n=10):
        """Movies sharing the most genres with the selected movie."""
        genres = self.genres_of(movie)
        if not genres:
            return self.by_similarity(movie, n)
        ranked = []
        for title in self.titles:
            if title == movie:
                continue
            overlap = set(self.genres_of(title)) & set(genres)
            if overlap:
                ranked.append((title, len(overlap)))
        ranked.sort(key=lambda x: x[1], reverse=True)
        results = []
        for title, score in ranked[:n]:
            results.append(
                {
                    "title": title,
                    "score": score,
                    "id": self.movie_id_of(title),
                }
            )
        return results

    def curated(self, n=10):
        """A small curated set of broadly popular titles."""
        curated_titles = [
            "Avatar", "Titanic", "Inception", "The Dark Knight",
            "Interstellar", "The Lord of the Rings: The Return of the King",
            "The Shawshank Redemption", "Jurassic Park", "The Matrix",
            "Gladiator", "Forrest Gump", "The Avengers",
            "Pulp Fiction", "The Silence of the Lambs", "Fight Club",
            "The Godfather", "Star Wars: Episode VII - The Force Awakens",
            "Mad Max: Fury Road", "The Lion King", "Toy Story",
        ]
        found = [t for t in curated_titles if t in self.titles]
        results = [
            {"title": t, "score": None, "id": self.movie_id_of(t)}
            for t in found[:n]
        ]
        if len(results) < n:
            sample = random.sample(
                self.titles, min(n - len(results), len(self.titles))
            )
            results += [
                {"title": t, "score": None, "id": self.movie_id_of(t)}
                for t in sample
            ]
        return results


_engine_instance = None


def get_engine():
    """Return a lazily cached singleton engine."""
    global _engine_instance
    if _engine_instance is None:
        movies, similarity = load_data()
        _engine_instance = Recommender(movies, similarity)
    return _engine_instance
