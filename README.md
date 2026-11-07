# CineScope Pro — Movie Recommender

An offline, content-based movie discovery application built with Streamlit. It uses movie metadata and text features to find titles with similar themes and attributes.

> This repository is an individual project and is currently featured as CineScope in the [portfolio](https://hiialiasgar.github.io/HiiAliasgar/).

## Features

- Content-based movie matching.
- Genre exploration and genre-weighted discovery.
- Curated popular and classic movie collections.
- Movie details including available synopsis, release information and ratings.
- Poster and metadata retrieval with local caching.
- Automatic generation of recommendation artifacts when they are missing.

## Recommendation approach

1. Combine available overview, genre, cast and crew keywords into text tags.
2. Normalize text using the configured preprocessing pipeline.
3. Vectorize tags with scikit-learn's `CountVectorizer`.
4. Calculate cosine similarity between movie vectors.
5. Rank candidate titles by similarity and the selected discovery mode.

The project stores the similarity matrix using `float32` values to reduce memory use.

## Technology

- Python 3.10+
- Streamlit
- pandas
- scikit-learn
- TMDB metadata/poster integration

## Run locally

```bash
git clone https://github.com/HiiAliasgar/Moive-Recommender-System.git
cd Moive-Recommender-System
pip install -r requirements.txt
python -m pytest -q  # run unit tests first
streamlit run app.py
```

The first run may generate the vectorizer and similarity artifacts if they are not already present. External poster or metadata requests depend on network availability.

## Main files

```text
app.py              # Streamlit interface
recommender.py      # Recommendation logic
tmdb_client.py      # Poster and metadata client
build_model.py      # Feature and similarity artifact generation
moive.pkl           # Movie metadata dataset
model/              # Generated recommendation artifacts
```

## Tests

Run the recommendation-engine unit tests with `python -m pytest -q`. The tests use a small synthetic dataset and do not need the full movie metadata file or TMDB credentials.

## Limitations

Recommendations are based on available metadata and content similarity; they do not represent user-personalized collaborative filtering. Results depend on dataset coverage and metadata quality.

[Source code](https://github.com/HiiAliasgar/Moive-Recommender-System)
