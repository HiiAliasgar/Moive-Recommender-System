"""CineScope Pro — Cinema-Grade Movie Recommender System.

Features:
- Responsive, dark-themed cinematic UI (Apple TV+ / Letterboxd inspired)
- Multi-threaded TMDB poster & metadata engine with DNS bypass and disk caching
- Interactive movie cards with match-score badges, ratings, and genre tags
- Rich Movie Details dialog (st.dialog) with synopsis, runtime, and "Find Similar" pivot
- Multi-mode discovery: Movie Matcher, Genre Blend, Genre Explorer, Hall of Fame, and Movie Roulette
"""

import html
import random
import warnings

import streamlit as st

from recommender import get_engine
from tmdb_client import fetch_movies_batch, get_movie_details

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CineScope Pro • AI Movie Discovery",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — Cinematic Dark Theme
# ---------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.stApp {
    background: radial-gradient(circle at 50% -10%, #1e293b 0%, #0a0e17 60%, #050811 100%);
    color: #f1f5f9;
}

[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1350px; }

/* Hero Banner */
.hero-container {
    text-align: center;
    padding: 2rem 1.5rem 1.2rem 1.5rem;
    margin-bottom: 1.5rem;
    background: rgba(17, 24, 39, 0.45);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
}
.hero-title {
    font-size: 2.8rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 45%, #f97316 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    display: inline-block;
}
.hero-subtitle {
    color: #94a3b8;
    font-size: 1.05rem;
    font-weight: 500;
    margin-top: 0.4rem;
}
.hero-stats {
    display: inline-flex;
    gap: 1.2rem;
    margin-top: 0.8rem;
    padding: 0.35rem 1rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 999px;
    font-size: 0.8rem;
    color: #cbd5e1;
    border: 1px solid rgba(255, 255, 255, 0.06);
}

/* Seed Movie Feature Banner */
.seed-banner {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.75) 0%, rgba(15, 23, 42, 0.85) 100%);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: 16px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.45);
}
.seed-poster {
    width: 80px;
    height: 120px;
    border-radius: 8px;
    object-fit: cover;
    box-shadow: 0 6px 16px rgba(0,0,0,0.5);
    flex-shrink: 0;
}
.seed-info {
    flex: 1;
}
.seed-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: #f8fafc;
    margin: 0;
}
.seed-meta {
    color: #f59e0b;
    font-size: 0.85rem;
    font-weight: 600;
    margin-top: 0.2rem;
}
.seed-overview {
    color: #94a3b8;
    font-size: 0.85rem;
    line-height: 1.4;
    margin-top: 0.4rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

/* Movie Card Styles */
.movie-card-wrapper {
    background: #111827;
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    overflow: hidden;
    transition: all 0.26s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
    margin-bottom: 0.4rem;
    position: relative;
    display: flex;
    flex-direction: column;
}
.movie-card-wrapper:hover {
    transform: translateY(-6px) scale(1.015);
    border-color: rgba(245, 158, 11, 0.5);
    box-shadow: 0 16px 32px rgba(0, 0, 0, 0.6), 0 0 20px rgba(245, 158, 11, 0.2);
}

.poster-box {
    position: relative;
    width: 100%;
    aspect-ratio: 2 / 3;
    overflow: hidden;
    background: #1a2234;
}
.poster-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    transition: transform 0.35s ease;
}
.movie-card-wrapper:hover .poster-img {
    transform: scale(1.05);
}

.badge-match {
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(16, 185, 129, 0.92);
    color: #ffffff;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 999px;
    backdrop-filter: blur(6px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}
.badge-rating {
    position: absolute;
    top: 8px;
    left: 8px;
    background: rgba(15, 23, 42, 0.88);
    border: 1px solid rgba(245, 158, 11, 0.6);
    color: #fbbf24;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 999px;
    backdrop-filter: blur(6px);
}

.card-content {
    padding: 0.75rem 0.8rem 0.5rem 0.8rem;
    display: flex;
    flex-direction: column;
    flex-grow: 1;
}
.card-title {
    font-size: 0.92rem;
    font-weight: 700;
    color: #f8fafc;
    line-height: 1.25;
    height: 2.4rem;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    margin-bottom: 0.35rem;
}
.genre-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 0.3rem;
    height: 1.5rem;
    overflow: hidden;
}
.chip-tag {
    background: rgba(255, 255, 255, 0.08);
    color: #cbd5e1;
    font-size: 0.68rem;
    font-weight: 600;
    padding: 1px 6px;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}

/* Offline / Fallback Poster */
.poster-fallback {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: linear-gradient(145deg, #1e293b, #0f172a);
    color: #94a3b8;
    text-align: center;
    padding: 1rem;
    box-sizing: border-box;
}
.poster-fallback-icon {
    font-size: 2.4rem;
    margin-bottom: 0.4rem;
    opacity: 0.8;
}
.poster-fallback-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: #e2e8f0;
    line-height: 1.3;
}

/* Section Title */
.section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 1.8rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.section-title {
    font-size: 1.35rem;
    font-weight: 800;
    color: #f8fafc;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Sidebar Customization */
[data-testid="stSidebar"] {
    background: #0d121f;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
    color: #f59e0b;
}

/* Buttons */
div.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    transition: all 0.2s ease;
    width: 100%;
}
div.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #f59e0b, #ea580c);
    color: #0b0f1a;
    border: none;
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.35);
}
div.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(245, 158, 11, 0.5);
    color: #000;
}
div.stButton > button[kind="secondary"] {
    background: rgba(255, 255, 255, 0.06);
    color: #f1f5f9;
    border: 1px solid rgba(255, 255, 255, 0.12);
}
div.stButton > button[kind="secondary"]:hover {
    background: rgba(255, 255, 255, 0.12);
    border-color: #f59e0b;
    color: #f59e0b;
}

footer { visibility: hidden; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Engine Loader
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Initializing recommendation engine…")
def load_engine():
    return get_engine()


try:
    engine = load_engine()
except Exception as exc:
    st.error(f"Failed to load recommendation engine: {exc}")
    st.stop()


# ---------------------------------------------------------------------------
# State Management
# ---------------------------------------------------------------------------
if "selected_movie" not in st.session_state:
    st.session_state["selected_movie"] = "Inception"
if "mode" not in st.session_state:
    st.session_state["mode"] = "similar"
if "active_dialog_movie" not in st.session_state:
    st.session_state["active_dialog_movie"] = None


# ---------------------------------------------------------------------------
# Movie Details Dialog (st.dialog)
# ---------------------------------------------------------------------------
@st.dialog("🎬 Movie Overview", width="large")
def show_movie_dialog(movie):
    """Rich popup modal displaying synopsis, poster, rating, and quick pivot button."""
    cols = st.columns([1, 2], gap="large")
    with cols[0]:
        if movie.get("poster_url"):
            st.image(movie["poster_url"], use_container_width=True)
        else:
            st.markdown(render_poster_fallback_html(movie["title"]), unsafe_allow_html=True)

    with cols[1]:
        st.markdown(f"## {movie['title']}")
        if movie.get("tagline"):
            st.markdown(f"*{movie['tagline']}*")

        meta = []
        if movie.get("release_year"):
            meta.append(f"📅 **{movie['release_year']}**")
        if movie.get("runtime"):
            hours = movie["runtime"] // 60
            mins = movie["runtime"] % 60
            meta.append(f"⏱️ **{hours}h {mins}m**" if hours else f"⏱️ **{mins}m**")
        if movie.get("vote_average"):
            meta.append(f"⭐ **{movie['vote_average']} / 10** ({movie.get('vote_count', 0):,} votes)")
        if meta:
            st.markdown(" • ".join(meta))

        genres = movie.get("genres", [])
        if genres:
            pills = " ".join([f"`{g}`" for g in genres])
            st.markdown(f"**Genres:** {pills}")

        st.markdown("---")
        overview = movie.get("overview")
        if overview:
            st.markdown("#### Storyline")
            st.write(overview)
        else:
            tags = engine.tags_of(movie["title"])
            if tags:
                st.markdown("#### Keywords & Theme")
                st.write(tags[:300] + "…")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🎯 Recommend Movies Like This", key=f"pivot_{movie.get('id', movie['title'])}", type="primary"):
                st.session_state["selected_movie"] = movie["title"]
                st.session_state["mode"] = "similar"
                st.rerun()
        with col_b:
            if movie.get("tmdb_url"):
                st.link_button("🌐 View on TMDB", movie["tmdb_url"], use_container_width=True)


# ---------------------------------------------------------------------------
# HTML Helpers
# ---------------------------------------------------------------------------
def render_poster_fallback_html(title):
    escaped_title = html.escape(title)
    return f"""
    <div class="poster-fallback">
        <div class="poster-fallback-icon">🎬</div>
        <div class="poster-fallback-title">{escaped_title}</div>
    </div>
    """


def render_card_html(item):
    title = html.escape(item.get("title", "Untitled"))
    poster_url = item.get("poster_url")
    score = item.get("score")
    vote_avg = item.get("vote_average")
    genres = item.get("genres") or engine.genres_of(item.get("title", ""))

    genre_chips = "".join([f'<span class="chip-tag">{html.escape(g)}</span>' for g in genres[:3]])

    match_badge = ""
    if score is not None:
        match_badge = f'<div class="badge-match">{score:.0%} Match</div>'

    rating_badge = ""
    if vote_avg is not None and vote_avg > 0:
        rating_badge = f'<div class="badge-rating">★ {vote_avg:.1f}</div>'

    if poster_url:
        poster_content = f'<img src="{poster_url}" class="poster-img" loading="lazy" alt="{title}">'
    else:
        poster_content = render_poster_fallback_html(title)

    return f"""
    <div class="movie-card-wrapper">
        <div class="poster-box">
            {poster_content}
            {match_badge}
            {rating_badge}
        </div>
        <div class="card-content">
            <div class="card-title" title="{title}">{title}</div>
            <div class="genre-chips">{genre_chips}</div>
        </div>
    </div>
    """


def render_movie_grid(raw_items, cols_count=5):
    """Concurrently hydrate movie details and render into a responsive grid."""
    if not raw_items:
        st.info("No movie recommendations found.")
        return

    with st.spinner("Loading posters and movie details…"):
        items = fetch_movies_batch(raw_items)

    rows = (len(items) + cols_count - 1) // cols_count
    for row in range(rows):
        cards = st.columns(cols_count, gap="medium")
        for col in range(cols_count):
            idx = row * cols_count + col
            if idx < len(items):
                item = items[idx]
                with cards[col]:
                    st.markdown(render_card_html(item), unsafe_allow_html=True)
                    if st.button("Details", key=f"det_{item.get('id', idx)}_{idx}", type="secondary"):
                        show_movie_dialog(item)


# ---------------------------------------------------------------------------
# Hero Header
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="hero-container">
        <h1 class="hero-title">🎬 CineScope Pro</h1>
        <div class="hero-subtitle">Next-Generation Movie Discovery & AI Recommendation Engine</div>
        <div class="hero-stats">
            <span>📚 <b>{len(engine.titles):,}</b> Movies Indexed</span>
            <span>⚡ <b>Instant</b> Offline Cosine Filtering</span>
            <span>🎨 <b>HD</b> Posters & Metadata</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar Controls
# ---------------------------------------------------------------------------
st.sidebar.markdown("### 🎛️ Discovery Controls")

MODE_OPTIONS = {
    "similar": "🎯 Movie Matcher",
    "genre_similar": "🎭 Genre Blend",
    "browse": "🧭 Genre Explorer",
    "curated": "🌟 Hall of Fame",
    "roulette": "🎲 Movie Roulette",
}

current_mode_index = list(MODE_OPTIONS.keys()).index(st.session_state["mode"]) if st.session_state["mode"] in MODE_OPTIONS else 0
selected_mode = st.sidebar.radio(
    "Discovery Mode",
    list(MODE_OPTIONS.keys()),
    index=current_mode_index,
    format_func=MODE_OPTIONS.get,
)
st.session_state["mode"] = selected_mode

count = st.sidebar.slider("Number of Recommendations", 3, 20, 10, step=1)
grid_cols = st.sidebar.select_slider("Grid Density (Columns)", options=[3, 4, 5, 6], value=5)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style='color:#94a3b8; font-size:0.8rem; line-height:1.5;'>
        <b>CineScope Pro</b> leverages TF-IDF and bag-of-words vectorization across plot keywords, cast, and genres to compute high-accuracy similarity metrics.
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Mode 1: Similar to a Movie (Movie Matcher)
# ---------------------------------------------------------------------------
if selected_mode == "similar":
    st.markdown('<div class="section-header"><div class="section-title">🎯 Movie Matcher</div></div>', unsafe_allow_html=True)
    st.markdown("<small style='color:#94a3b8'>Select or type your favorite film to find titles with matching storyline, cast, and atmosphere.</small>", unsafe_allow_html=True)

    # Quick Pick Chips
    st.markdown("**🔥 Quick Picks:**")
    quick_cols = st.columns(6)
    quick_titles = ["Inception", "Interstellar", "The Dark Knight", "Avatar", "The Matrix", "Gladiator"]
    for i, q_title in enumerate(quick_titles):
        with quick_cols[i]:
            if st.button(q_title, key=f"quick_{q_title}", type="secondary"):
                st.session_state["selected_movie"] = q_title
                st.rerun()

    # Autocomplete Search
    search_query = st.text_input("🔍 Search Movie Library", placeholder="e.g. Inception, Avatar, Titanic, Interstellar…")
    search_results = engine.search(search_query, limit=15) if search_query.strip() else []

    if search_results:
        default_idx = 0
        if st.session_state["selected_movie"] in search_results:
            default_idx = search_results.index(st.session_state["selected_movie"])
        selected_movie = st.selectbox("Select Matching Title", search_results, index=default_idx)
        st.session_state["selected_movie"] = selected_movie
    else:
        # Default selectbox from top popular titles
        popular_pool = ["Inception", "Interstellar", "The Dark Knight", "Avatar", "The Matrix", "Titanic", "Gladiator", "Forrest Gump", "Pulp Fiction", "The Avengers"]
        options = sorted(list(set(popular_pool + [st.session_state["selected_movie"]])))
        def_idx = options.index(st.session_state["selected_movie"]) if st.session_state["selected_movie"] in options else 0
        selected_movie = st.selectbox("Current Selected Movie", options, index=def_idx)
        st.session_state["selected_movie"] = selected_movie

    # Seed Movie Banner
    seed_details = get_movie_details(engine.movie_id_of(selected_movie), selected_movie)
    seed_poster_url = seed_details.get("poster_url")
    seed_year = seed_details.get("release_year", "")
    seed_vote = seed_details.get("vote_average", "")
    seed_genres = " • ".join(seed_details.get("genres", engine.genres_of(selected_movie)))
    seed_overview = seed_details.get("overview") or engine.tags_of(selected_movie)[:250] + "…"

    seed_poster_html = f'<img src="{seed_poster_url}" class="seed-poster">' if seed_poster_url else ''

    st.markdown(
        f"""
        <div class="seed-banner">
            {seed_poster_html}
            <div class="seed-info">
                <div class="seed-title">Matching with: {html.escape(selected_movie)}</div>
                <div class="seed-meta">{html.escape(seed_genres)} {f'| {seed_year}' if seed_year else ''} {f'| ⭐ {seed_vote}/10' if seed_vote else ''}</div>
                <div class="seed-overview">{html.escape(seed_overview)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f'<div class="section-title">✨ Top Matches for "{selected_movie}"</div>', unsafe_allow_html=True)
    recommendations = engine.by_similarity(selected_movie, n=count)
    render_movie_grid(recommendations, cols_count=grid_cols)

# ---------------------------------------------------------------------------
# Mode 2: Genre Blend (Same Favorites)
# ---------------------------------------------------------------------------
elif selected_mode == "genre_similar":
    st.markdown('<div class="section-header"><div class="section-title">🎭 Genre Blend</div></div>', unsafe_allow_html=True)
    st.markdown("<small style='color:#94a3b8'>Find titles that share the exact genre DNA and themes of your favorite film.</small>", unsafe_allow_html=True)

    popular_pool = ["The Dark Knight", "Inception", "The Avengers", "Avatar", "Jurassic Park", "Toy Story", "The Matrix"]
    options = sorted(list(set(popular_pool + [st.session_state["selected_movie"]])))
    def_idx = options.index(st.session_state["selected_movie"]) if st.session_state["selected_movie"] in options else 0
    selected_movie = st.selectbox("Pick Seed Movie", options, index=def_idx)

    seed_genres = engine.genres_of(selected_movie)
    if seed_genres:
        st.info(f"Target Genres for **{selected_movie}**: {', '.join(seed_genres)}")

    recommendations = engine.by_genre_similar(selected_movie, n=count)
    render_movie_grid(recommendations, cols_count=grid_cols)

# ---------------------------------------------------------------------------
# Mode 3: Browse by Genre (Genre Explorer)
# ---------------------------------------------------------------------------
elif selected_mode == "browse":
    st.markdown('<div class="section-header"><div class="section-title">🧭 Genre Explorer</div></div>', unsafe_allow_html=True)

    ALL_GENRES = [
        "Action", "Adventure", "Animation", "Comedy", "Crime",
        "Drama", "Family", "Fantasy", "History", "Horror",
        "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western",
    ]

    selected_genre = st.selectbox("Choose Genre", ALL_GENRES, index=ALL_GENRES.index("Sci-Fi") if "Sci-Fi" in ALL_GENRES else 0)

    col_btn, _ = st.columns([1, 4])
    with col_btn:
        reshuffle = st.button("🔄 Shuffle Titles", type="secondary")

    recommendations = engine.by_genre(selected_genre, n=count)
    render_movie_grid(recommendations, cols_count=grid_cols)

# ---------------------------------------------------------------------------
# Mode 4: Curated Picks (Hall of Fame)
# ---------------------------------------------------------------------------
elif selected_mode == "curated":
    st.markdown('<div class="section-header"><div class="section-title">🌟 Cinema Hall of Fame</div></div>', unsafe_allow_html=True)
    st.markdown("<small style='color:#94a3b8'>Critically acclaimed cinematic masterpieces and worldwide box-office titans.</small>", unsafe_allow_html=True)

    recommendations = engine.curated(n=count)
    render_movie_grid(recommendations, cols_count=grid_cols)

# ---------------------------------------------------------------------------
# Mode 5: Movie Roulette (Surprise Me)
# ---------------------------------------------------------------------------
elif selected_mode == "roulette":
    st.markdown('<div class="section-header"><div class="section-title">🎲 Movie Roulette</div></div>', unsafe_allow_html=True)
    st.markdown("<small style='color:#94a3b8'>Feeling lucky? Spin the reel to discover random gems from across the library.</small>", unsafe_allow_html=True)

    if st.button("🎰 Spin the Reel (Surprise Me!)", type="primary"):
        st.session_state["roulette_seed"] = random.randint(1, 100000)

    recommendations = engine.random_discovery(n=count)
    render_movie_grid(recommendations, cols_count=grid_cols)
