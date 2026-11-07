import unittest

import numpy as np
import pandas as pd

from recommender import Recommender, extract_genres


def make_engine():
    movies = pd.DataFrame(
        [
            {"title": "Alpha", "tags": "Action Adventure space", "movie_id": 1},
            {"title": "Beta", "tags": "Action Crime city", "movie_id": 2},
            {"title": "Gamma", "tags": "Drama Romance", "movie_id": 3},
            {"title": "Delta", "tags": "Action Adventure", "movie_id": 4},
        ]
    )
    similarity = np.array(
        [
            [1.0, 0.8, 0.1, 0.7],
            [0.8, 1.0, 0.2, 0.5],
            [0.1, 0.2, 1.0, 0.1],
            [0.7, 0.5, 0.1, 1.0],
        ],
        dtype=np.float32,
    )
    return Recommender(movies, similarity)


class RecommenderTests(unittest.TestCase):
    def setUp(self):
        self.engine = make_engine()

    def test_title_search_is_case_insensitive(self):
        self.assertEqual(self.engine.search("  alP "), ["Alpha"])
        self.assertEqual(self.engine.search(None), [])

    def test_tags_of_returns_tags_for_known_title(self):
        self.assertEqual(self.engine.tags_of("alpha"), "Action Adventure space")
        self.assertEqual(self.engine.tags_of("missing"), "")

    def test_similarity_excludes_selected_movie_and_resolves_case(self):
        results = self.engine.by_similarity("alpha", n=2)
        self.assertEqual([item["title"] for item in results], ["Beta", "Delta"])
        self.assertNotIn("Alpha", [item["title"] for item in results])

    def test_zero_result_limit_returns_empty_list(self):
        self.assertEqual(self.engine.by_similarity("Alpha", n=0), [])
        self.assertEqual(self.engine.by_genre("Action", n=0), [])
        self.assertEqual(self.engine.by_genre_similar("Alpha", n=0), [])
        self.assertEqual(self.engine.curated(n=0), [])
        self.assertEqual(self.engine.random_discovery(n=0), [])

    def test_negative_result_limit_is_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.by_similarity("Alpha", n=-1)
        with self.assertRaises(ValueError):
            self.engine.random_discovery(n=-1)

    def test_genre_recommendations_are_nonempty(self):
        results = self.engine.by_genre("Action", n=10)
        self.assertTrue(results)
        self.assertTrue(all("Action" in item["genres"] for item in results))

    def test_genre_similarity_resolves_case(self):
        results = self.engine.by_genre_similar("alpha", n=2)
        self.assertEqual(len(results), 2)
        self.assertNotIn("Alpha", [item["title"] for item in results])

    def test_invalid_model_matrix_shape_is_rejected(self):
        movies = self.engine.movies
        with self.assertRaisesRegex(ValueError, "dimensions"):
            Recommender(movies, np.zeros((2, 2)))

    def test_genre_extraction_handles_missing_values(self):
        self.assertEqual(extract_genres(None), [])
        self.assertIn("Adventure", extract_genres("Action Adventure"))


if __name__ == "__main__":
    unittest.main()
