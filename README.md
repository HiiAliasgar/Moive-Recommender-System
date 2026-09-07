# 🎬 CineScope — Movie Recommender System

A professional-grade, **offline content-based movie recommender** with a polished, dark-themed Streamlit UI. Discover movies similar to your favourites, explore by genre, or browse curated picks — all powered by pre-computed content similarity.

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.63+-FF4B4B?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## ✨ Features

- **🔍 Similar to a movie** — content-based filtering that finds the titles closest to the one you pick (cosine similarity over tag vectors).
- **🎭 Same favourites** — discover movies that share the same genres as a title you love.
- **🧭 Browse by genre** — explore popular titles across a genre of your choice.
- **🌟 Curated picks** — a hand-picked set of well-known crowd favourites.
- **🎨 Polished UI** — a custom dark theme with gold/orange accents, a responsive card grid, and elegant offline poster placeholders.
- **⚡ Fast & offline** — all computation happens locally from pre-computed artifacts; no API keys or network required.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** (recommended) or `pip`

### 1. Clone the repository

```bash
git clone https://github.com/HiiAliasgar/Moive-Recommender-System.git
cd Moive-Recommender-System
```

### 2. Install dependencies

```bash
uv sync
```

> Without `uv`, create a venv and install manually:
> ```bash
> python -m venv .venv
> . .venv/bin/activate        # Windows: .venv\Scripts\activate
> pip install numpy pandas scikit-learn streamlit requests
> ```

### 3. Build the model artifacts

The large similarity matrix is generated locally (it exceeds GitHub's 100 MB file limit, so it is not stored in the repo):

```bash
python build_model.py
```

This reads the raw `moive.pkl` source data and writes:

```
model/
├── movie_list.pkl      # serialized movie DataFrame (title, tags, movie_id)
└── similarity.pkl      # cosine-similarity matrix
```

### 4. Run the app

```bash
streamlit run app.py
```

Your browser will open at `http://localhost:8501`.

---

## 🖥️ Usage

1. Choose a **recommendation mode** from the sidebar.
2. Adjust **how many recommendations** you'd like (1–10).
3. Follow the on-screen prompts:
   - **Similar to a movie** / **Same favourites**: start typing a title, select it, then click **Show recommendations**.
   - **Browse by genre**: pick a genre and click **Explore**.
   - **Curated picks**: recommendations appear immediately.

---

## 🏗️ Project Structure

```
├── app.py                  # Streamlit web UI (CineScope)
├── recommender.py          # Core recommendation engine
├── build_model.py          # Builds model/*.pkl artifacts from raw data
├── moive.pkl               # Raw source dataset (pickled DataFrame)
├── model/                  # Generated artifacts (excluded from git)
│   ├── movie_list.pkl
│   └── similarity.pkl
├── pyproject.toml          # Project metadata + dependencies
└── uv.lock                 # Locked dependency versions
```

---

## 🧠 How It Works

1. **Feature engineering** — each movie's `tags` (description + keywords) are vectorized with `CountVectorizer` (`build_model.py`).
2. **Similarity** — a cosine-similarity matrix is computed across all tag vectors and cached as `model/similarity.pkl`.
3. **Recommendation** — given a seed movie, the engine ranks every other movie by its similarity score or genre overlap (`recommender.py`).

Because everything is pre-computed, lookups are instant and the app runs fully offline.

---

## 🛠️ Tech Stack

| Component     | Tool                                   |
|---------------|----------------------------------------|
| Language      | Python 3.13                            |
| UI            | [Streamlit](https://streamlit.io/)     |
| Data / ML     | pandas, NumPy, scikit-learn            |
| Web client    | requests (HTTP)                        |
| Environment   | uv + `pyproject.toml`                  |

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<p align="center">
  <sub>Built with 🎬 by <a href="https://github.com/HiiAliasgar">Aliasgar Lohawala</a></sub>
</p>
