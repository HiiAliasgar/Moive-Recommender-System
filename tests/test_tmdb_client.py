import unittest
from unittest.mock import patch

import tmdb_client


class TmdbClientTests(unittest.TestCase):
    def test_missing_api_key_skips_external_request(self):
        with patch.object(tmdb_client, "TMDB_API_KEY", None), patch.object(tmdb_client.requests, "get") as get:
            self.assertIsNone(tmdb_client.fetch_tmdb_details(42))
        get.assert_not_called()

    def test_api_key_is_sent_as_a_request_parameter_not_in_url(self):
        response = unittest.mock.Mock()
        response.status_code = 200
        response.json.return_value = {
            "title": "Example",
            "poster_path": "/poster.jpg",
            "backdrop_path": None,
            "release_date": "2024-01-01",
            "genres": [{"name": "Drama"}],
            "vote_average": 7.5,
            "vote_count": 10,
            "overview": "An example movie.",
        }
        with patch.object(tmdb_client, "TMDB_API_KEY", "test-secret"), patch.object(
            tmdb_client.requests, "get", return_value=response
        ) as get:
            result = tmdb_client.fetch_tmdb_details(42)

        request_url = get.call_args.args[0]
        self.assertNotIn("test-secret", request_url)
        self.assertEqual(get.call_args.kwargs["params"]["api_key"], "test-secret")
        self.assertEqual(result["title"], "Example")
        self.assertEqual(result["vote_average"], 7.5)


if __name__ == "__main__":
    unittest.main()
