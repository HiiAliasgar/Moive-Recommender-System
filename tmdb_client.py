"""Resilient TMDB and Wikipedia client for movie posters and metadata.

Features:
- DNS-over-HTTPS / CloudFront IP bypass for ISP-level DNS blocks on api.themoviedb.org
- Thread-pooled concurrent batch fetching for sub-second UI response
- Multi-tier caching: in-memory LRU + persistent local disk JSON cache
- Wikipedia REST summary API fallback
- Graceful offline fallback
"""

import json
import logging
import os
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

import requests
import urllib3
from urllib3.util import connection

urllib3.disable_warnings()
logger = logging.getLogger(__name__)

# Fallback AWS IPs for api.themoviedb.org if local ISP DNS poisons the domain
TMDB_FALLBACK_IPS = [
    "3.175.86.67",
    "3.175.86.103",
    "3.175.86.37",
    "3.175.86.50",
]

_ORIG_CREATE_CONNECTION = connection.create_connection


def _patched_create_connection(address, *args, **kwargs):
    host, port = address
    if host == "api.themoviedb.org":
        # Route to AWS CloudFront IP to bypass regional ISP DNS blocks
        return _ORIG_CREATE_CONNECTION((TMDB_FALLBACK_IPS[0], port), *args, **kwargs)
    return _ORIG_CREATE_CONNECTION(address, *args, **kwargs)


# Apply connection patch for requests to api.themoviedb.org
try:
    connection.create_connection = _patched_create_connection
except Exception as e:
    logger.warning("Could not patch urllib3 connection: %s", e)

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "movie_metadata.json")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
if not TMDB_API_KEY:
    logger.warning(
        "TMDB_API_KEY not set. Movie posters and metadata will be unavailable. "
        "Get a free key at https://www.themoviedb.org/settings/api"
    )
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
TMDB_BACKDROP_BASE = "https://image.tmdb.org/t/p/w780"

_DISK_CACHE = {}


def _load_disk_cache():
    global _DISK_CACHE
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as fh:
                _DISK_CACHE = json.load(fh)
        except Exception:
            _DISK_CACHE = {}


def _save_disk_cache():
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as fh:
            json.dump(_DISK_CACHE, fh, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning("Failed to save disk cache: %s", e)


_load_disk_cache()


def fetch_tmdb_details(movie_id):
    """Fetch movie details and poster path from TMDB API."""
    if not movie_id:
        return None
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    headers = {
        "User-Agent": "CineScope/2.0 (MovieRecommender)",
        "Host": "api.themoviedb.org",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=4)
        if resp.status_code == 200:
            data = resp.json()
            poster_path = data.get("poster_path")
            backdrop_path = data.get("backdrop_path")
            release_date = data.get("release_date", "")
            release_year = release_date[:4] if release_date else ""
            genres = [g.get("name") for g in data.get("genres", []) if g.get("name")]
            vote_avg = data.get("vote_average")
            vote_count = data.get("vote_count", 0)

            return {
                "id": movie_id,
                "title": data.get("title", ""),
                "poster_url": f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None,
                "backdrop_url": f"{TMDB_BACKDROP_BASE}{backdrop_path}" if backdrop_path else None,
                "vote_average": round(float(vote_avg), 1) if vote_avg is not None else None,
                "vote_count": vote_count,
                "release_year": release_year,
                "release_date": release_date,
                "overview": data.get("overview") or "",
                "tagline": data.get("tagline") or "",
                "genres": genres,
                "runtime": data.get("runtime"),
                "tmdb_url": f"https://www.themoviedb.org/movie/{movie_id}",
            }
    except Exception as exc:
        logger.debug("TMDB fetch failed for %s: %s", movie_id, exc)
    return None


def fetch_wikipedia_details(title):
    """Fallback: Fetch movie thumbnail and extract from Wikipedia REST API."""
    if not title:
        return None

    headers = {"User-Agent": "CineScope/2.0 (contact@example.com)"}
    candidates = [
        f"{title} (film)",
        title,
    ]
    for cand in candidates:
        slug = urllib.parse.quote(cand.replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
        try:
            resp = requests.get(url, headers=headers, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                thumb = data.get("thumbnail", {}).get("source")
                extract = data.get("extract", "")
                if thumb or extract:
                    return {
                        "poster_url": thumb,
                        "overview": extract,
                        "wiki_url": data.get("content_urls", {}).get("desktop", {}).get("page"),
                    }
        except Exception:
            continue
    return None


@lru_cache(maxsize=1024)
def get_movie_details(movie_id, title):
    """Retrieve full movie details with caching across memory and disk."""
    cache_key = str(movie_id) if movie_id else title
    if cache_key in _DISK_CACHE:
        return _DISK_CACHE[cache_key]

    details = None
    if movie_id:
        details = fetch_tmdb_details(movie_id)

    if not details or not details.get("poster_url"):
        wiki = fetch_wikipedia_details(title)
        if wiki:
            if not details:
                details = {
                    "id": movie_id,
                    "title": title,
                    "poster_url": wiki.get("poster_url"),
                    "backdrop_url": None,
                    "vote_average": None,
                    "vote_count": 0,
                    "release_year": "",
                    "release_date": "",
                    "overview": wiki.get("overview", ""),
                    "tagline": "",
                    "genres": [],
                    "runtime": None,
                    "tmdb_url": f"https://www.themoviedb.org/movie/{movie_id}" if movie_id else None,
                }
            elif not details.get("poster_url") and wiki.get("poster_url"):
                details["poster_url"] = wiki["poster_url"]
            if not details.get("overview") and wiki.get("overview"):
                details["overview"] = wiki["overview"]

    if not details:
        details = {
            "id": movie_id,
            "title": title,
            "poster_url": None,
            "backdrop_url": None,
            "vote_average": None,
            "vote_count": 0,
            "release_year": "",
            "release_date": "",
            "overview": "",
            "tagline": "",
            "genres": [],
            "runtime": None,
            "tmdb_url": f"https://www.themoviedb.org/movie/{movie_id}" if movie_id else None,
        }

    _DISK_CACHE[cache_key] = details
    return details


def fetch_movies_batch(items, max_workers=6):
    """Fetch movie details concurrently for a batch of movie dicts [{'id': ..., 'title': ...}]."""
    results = [None] * len(items)
    to_fetch = []

    for idx, item in enumerate(items):
        mid = item.get("id")
        title = item.get("title", "")
        key = str(mid) if mid else title
        if key in _DISK_CACHE:
            res = dict(_DISK_CACHE[key])
            if item.get("score") is not None:
                res["score"] = item["score"]
            results[idx] = res
        else:
            to_fetch.append((idx, mid, title, item.get("score")))

    if to_fetch:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(get_movie_details, mid, title): (idx, score)
                for (idx, mid, title, score) in to_fetch
            }
            for future in as_completed(future_to_idx):
                idx, score = future_to_idx[future]
                try:
                    res = dict(future.result())
                    if score is not None:
                        res["score"] = score
                    results[idx] = res
                except Exception as exc:
                    logger.debug("Batch fetch task failed: %s", exc)
        _save_disk_cache()

    for idx, item in enumerate(items):
        if results[idx] is None:
            results[idx] = {
                "id": item.get("id"),
                "title": item.get("title", ""),
                "poster_url": None,
                "backdrop_url": None,
                "vote_average": None,
                "vote_count": 0,
                "release_year": "",
                "release_date": "",
                "overview": "",
                "tagline": "",
                "genres": [],
                "runtime": None,
                "score": item.get("score"),
                "tmdb_url": f"https://www.themoviedb.org/movie/{item.get('id')}" if item.get("id") else None,
            }
    return results
