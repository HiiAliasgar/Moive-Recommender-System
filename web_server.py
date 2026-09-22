"""Standalone lightweight HTTP web server for CineScope Pro.

Serves the modern frontend at http://localhost:8000 and exposes REST API endpoints:
- GET /api/search?q=<query>
- GET /api/recommend?movie=<title>&n=<count>
- GET /api/by-genre?genre=<name>&n=<count>
- GET /api/curated?n=<count>
- GET /api/details?movie=<title>
"""

import http.server
import json
import os
import socketserver
import urllib.parse
from functools import partial

from recommender import get_engine
from tmdb_client import fetch_movies_batch, get_movie_details

PORT = int(os.environ.get("PORT", 8000))
HERE = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(HERE, "static")

engine = get_engine()


class CineScopeHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path.startswith("/api/"):
            self.handle_api(path, params)
        else:
            if path == "/" or not os.path.exists(os.path.join(STATIC_DIR, path.lstrip("/"))):
                self.path = "/index.html"
            super().do_GET()

    def handle_api(self, path, params):
        data = None
        try:
            if path == "/api/search":
                q = params.get("q", [""])[0]
                limit = int(params.get("limit", [10])[0])
                titles = engine.search(q, limit=limit)
                data = [{"title": t, "id": engine.movie_id_of(t)} for t in titles]

            elif path == "/api/recommend":
                movie = params.get("movie", ["Inception"])[0]
                n = int(params.get("n", [10])[0])
                recs = engine.by_similarity(movie, n=n)
                data = fetch_movies_batch(recs)

            elif path == "/api/by-genre":
                genre = params.get("genre", ["Sci-Fi"])[0]
                n = int(params.get("n", [10])[0])
                recs = engine.by_genre(genre, n=n)
                data = fetch_movies_batch(recs)

            elif path == "/api/curated":
                n = int(params.get("n", [10])[0])
                recs = engine.curated(n=n)
                data = fetch_movies_batch(recs)

            elif path == "/api/details":
                movie = params.get("movie", [""])[0]
                mid = engine.movie_id_of(movie)
                data = get_movie_details(mid, movie)

            else:
                self.send_response(404)
                self.end_headers()
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

        except Exception as exc:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(exc)}).encode("utf-8"))


def run():
    os.makedirs(STATIC_DIR, exist_ok=True)
    with socketserver.TCPServer(("", PORT), CineScopeHandler) as httpd:
        print(f"CineScope Web Server running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    run()
