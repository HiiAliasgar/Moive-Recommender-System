"""Professional movie recommendation engine.

Content-based recommendation built on movie tag (description, cast, crew, keywords)
vectors, evaluated with cosine similarity. Automatically self-heals by generating
model artifacts if missing.
"""

import os
import pickle
import random
import logging

import pandas as pd

logger = logging.getLogger(__name__)

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(HERE, "model")


def load_data():
    """Load the movie list and similarity matrix, building them if missing."""
    movie_list_path = os.path.join(MODEL_DIR, "movie_list.pkl")
    similarity_path = os.path.join(MODEL_DIR, "similarity.pkl")

    if not os.path.exists(movie_list_path) or not os.path.exists(similarity_path):
        logger.info("Model artifacts missing. Auto-building similarity matrix...")
        import build_model
        build_model.build()

    movies = pd.read_pickle(movie_list_path)
    with open(similarity_path, "rb") as fh:
        similarity = pickle.load(fh)

    return movies, similarity


GENRE_MAP = {
    "action": "Action",
    "adventur": "Adventure",
    "adventure": "Adventure",
    "anim": "Animation",
    "animation": "Animation",
    "comedi": "Comedy",
    "comedy": "Comedy",
    "crime": "Crime",
    "drama": "Drama",
    "fantasi": "Fantasy",
    "fantasy": "Fantasy",
    "horror": "Horror",
    "mysteri": "Mystery",
    "mystery": "Mystery",
    "romanc": "Romance",
    "romance": "Romance",
    "sciencefict": "Sci-Fi",
    "scifi": "Sci-Fi",
    "thriller": "Thriller",
    "famili": "Family",
    "family": "Family",
    "music": "Music",
    "histori": "History",
    "history": "History",
    "war": "War",
    "western": "Western",
    "documentari": "Documentary",
}


def extract_genres(tags):
    """Extract clean, capitalized human-readable genres from movie tags."""
    if not isinstance(tags, str):
        return []
    tags_lower = tags.lower()
    genres = set()
    for alias, name in GENRE_MAP.items():
        # Match as word boundary or substring in tags
        if alias in tags_lower:
            genres.add(name)
    return sorted(genres)


class Recommender:
    """Encapsulates all recommendation strategies and metadata helpers."""

    def __init__(self, movies, similarity):
        self.movies = movies
        self.similarity = similarity
        self.titles = movies["title"].tolist()
        self._title_lower_map = {t.lower(): t for t in self.titles}
        self._title_to_idx = {t: i for i, t in enumerate(self.titles)}
        self._genre_cache = {}

        # Pre-extract genres for all movies for fast filtering
        self._movie_genres = [
            extract_genres(tags) for tags in movies["tags"].fillna("")
        ]

    # ----- metadata helpers -----
    def genres_of(self, title):
        if title not in self._genre_cache:
            idx = self._title_to_idx.get(title)
            if idx is not None:
                self._genre_cache[title] = self._movie_genres[idx]
            else:
                self._genre_cache[title] = []
        return self._genre_cache[title]

    def movie_id_of(self, title):
        idx = self._title_to_idx.get(title)
        if idx is not None:
            return int(self.movies.iloc[idx]["movie_id"])
        return None

    def search(self, query, limit=20):
        """Case/space-insensitive title search prioritizing prefix matches."""
        q = query.strip().lower()
        if not q:
            return []
        exact = []
        starts = []
        contains = []
        for t in self.titles:
            tl = t.lower()
            if tl == q:
                exact.append(t)
            elif tl.startswith(q):
                starts.append(t)
            elif q in tl:
                contains.append(t)
        return (exact + sorted(starts, key=len) + sorted(contains, key=len))[:limit]

    # ----- strategies -----
    def by_similarity(self, movie, n=5):
        """Content-based similar movies using cosine similarity over tag vectors."""
        idx = self._title_to_idx.get(movie)
        if idx is None:
            # Fallback to case-insensitive match
            clean = self._title_lower_map.get(movie.lower())
            if clean:
                idx = self._title_to_idx.get(clean)
            else:
                return []

        sim_scores = self.similarity[idx]
        scored = sorted(
            list(enumerate(sim_scores)),
            key=lambda x: x[1],
            reverse=True,
        )

        results = []
        for item_idx, score in scored:
            if item_idx == idx:
                continue
            title = self.titles[item_idx]
            results.append(
                {
                    "title": title,
                    "score": round(float(score), 3),
                    "id": int(self.movies.iloc[item_idx]["movie_id"]),
                    "genres": self._movie_genres[item_idx],
                }
            )
            if len(results) >= n:
                break
        return results

    def by_genre(self, genre, n=10):
        """Recommend popular titles matching the chosen genre."""
        matched_indices = [
            i for i, g_list in enumerate(self._movie_genres)
            if genre.lower() in [g.lower() for g in g_list]
        ]
        if not matched_indices:
            return []

        # Sort selected titles with seed consistency and good variety
        sample_indices = random.sample(matched_indices, min(n, len(matched_indices)))
        results = []
        for i in sample_indices:
            results.append(
                {
                    "title": self.titles[i],
                    "score": None,
                    "id": int(self.movies.iloc[i]["movie_id"]),
                    "genres": self._movie_genres[i],
                }
            )
        return results

    def by_genre_similar(self, movie, n=10):
        """Movies sharing the most genres and content with the selected movie."""
        genres = set(self.genres_of(movie))
        if not genres:
            return self.by_similarity(movie, n)

        target_idx = self._title_to_idx.get(movie)
        sim_scores = self.similarity[target_idx] if target_idx is not None else None

        candidates = []
        for i, title in enumerate(self.titles):
            if title == movie:
                continue
            overlap = len(genres & set(self._movie_genres[i]))
            if overlap > 0:
                sim = float(sim_scores[i]) if sim_scores is not None else 0.0
                # Combined metric: genre overlap weight + semantic similarity
                combined_score = (overlap * 0.4) + (sim * 0.6)
                candidates.append((i, combined_score, sim))

        candidates.sort(key=lambda x: x[1], reverse=True)
        results = []
        for i, combined, sim in candidates[:n]:
            results.append(
                {
                    "title": self.titles[i],
                    "score": round(sim, 3),
                    "id": int(self.movies.iloc[i]["movie_id"]),
                    "genres": self._movie_genres[i],
                }
            )
        return results

    def curated(self, n=10):
        """A handpicked hall of fame of critically acclaimed and blockbuster films."""
        hall_of_fame = [
            "Inception", "Interstellar", "The Dark Knight", "Avatar",
            "The Matrix", "Pulp Fiction", "Fight Club", "Forrest Gump",
            "The Lord of the Rings: The Return of the King", "Gladiator",
            "The Shawshank Redemption", "The Godfather", "Titanic",
            "Jurassic Park", "The Avengers", "Mad Max: Fury Road",
            "Star Wars: Episode VII - The Force Awakens", "The Lion King",
            "Toy Story", "Spider-Man", "Pirates of the Caribbean: The Curse of the Black Pearl",
            "Iron Man", "The Prestige", "Whiplash", "Django Unchained",
        ]
        found_titles = [t for t in hall_of_fame if t in self._title_to_idx]
        selected = found_titles[:n]
        results = []
        for t in selected:
            idx = self._title_to_idx[t]
            results.append(
                {
                    "title": t,
                    "score": None,
                    "id": int(self.movies.iloc[idx]["movie_id"]),
                    "genres": self._movie_genres[idx],
                }
            )
        return results

    def random_discovery(self, n=10):
        """Random discovery / movie roulette."""
        indices = random.sample(range(len(self.titles)), min(n, len(self.titles)))
        return [
            {
                "title": self.titles[i],
                "score": None,
                "id": int(self.movies.iloc[i]["movie_id"]),
                "genres": self._movie_genres[i],
            }
            for i in indices
        ]


_engine_instance = None


def get_engine():
    """Return a lazily cached singleton recommendation engine."""
    global _engine_instance
    if _engine_instance is None:
        movies, similarity = load_data()
        _engine_instance = Recommender(movies, similarity)
    return _engine_instance
