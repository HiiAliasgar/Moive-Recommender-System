# 🎬 CineScope Pro — AI Movie Recommender System

A cinema-grade, **offline content-based movie recommender** with a polished, dark-themed Streamlit UI (inspired by Apple TV+ and Letterboxd). Discover movies similar to your favorites, explore by genre blend, browse cinema halls of fame, or roll the movie roulette — with real high-definition posters, ratings, and synopses.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## ✨ Features

- **🎯 Movie Matcher** — Content-based filtering matching storyline keywords, cast, and atmosphere (using cosine similarity over tag vectors).
- **🎭 Genre Blend** — Discover movies sharing the exact genre DNA and themes of your favorite film.
- **🧭 Genre Explorer** — Interactive genre navigation (Sci-Fi, Action, Horror, Drama, Animation, etc.) with title shuffling.
- **🌟 Cinema Hall of Fame** — Handpicked timeless classics and box-office blockbusters.
- **🎲 Movie Roulette** — "Surprise Me" reel for spontaneous movie nights.
- **🖼️ Real High-Definition Posters** — Parallel batch poster retrieval with automatic DNS bypass (resilient against regional ISP DNS blocking) and persistent disk caching.
- **🎬 Movie Details Modal (`st.dialog`)** — Click any card to pop up official storylines, TMDB ratings (★), release years, runtimes, and a 1-click **"Recommend Movies Like This"** pivot button.
- **⚡ Self-Healing Architecture** — Automatically generates model artifacts if missing on first launch.

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/HiiAliasgar/Moive-Recommender-System.git
cd Moive-Recommender-System
```

### 2. Install dependencies

Using `pip`:
```bash
pip install -r requirements.txt
```
*(or with `uv`: `uv sync`)*

### 3. Run the application

```bash
streamlit run app.py
```

*Note: On first startup, CineScope Pro will automatically generate the cosine similarity matrix if not already present. No manual setup required!*

Your browser will open at `http://localhost:8501`.

---

## 🏗️ Project Architecture

```
├── app.py                  # CineScope Pro Streamlit Web UI
├── recommender.py          # Core recommendation engine (cosine similarity & self-healing)
├── tmdb_client.py          # Resilient poster & metadata client (DNS bypass + caching)
├── build_model.py          # Vectorizer & similarity matrix generator (float32 optimized)
├── moive.pkl               # TMDB 5000 movie dataset (DataFrame)
├── cache/                  # Persistent movie poster & metadata cache
│   └── movie_metadata.json
├── model/                  # Generated artifacts (auto-built if missing)
│   ├── movie_list.pkl
│   └── similarity.pkl
└── pyproject.toml          # Project configuration & dependencies
```

---

## 🧠 Recommendation Engine

1. **Tag Vectorization**: Movie overviews, genres, cast, and crew keywords are stemmed and vectorized with `CountVectorizer(max_features=5000, stop_words='english')`.
2. **Cosine Similarity**: Vector angles are computed into an all-pairs similarity matrix, stored as memory-efficient `float32`.
3. **Multi-Mode Ranking**: Recommends movies by vector proximity, combined genre-weight blending, or curated popularity.
4. **Smart Fallback**: Supports Wikipedia REST summary API and SVG cinema clapperboard rendering for uninterrupted offline playback.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

<p align="center">
  <sub>Built with 🎬 by <a href="https://github.com/HiiAliasgar">Aliasgar Lohawala</a></sub>
</p>
