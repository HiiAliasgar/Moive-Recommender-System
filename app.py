"""Movie Recommender System — Professional Edition.

An offline content-based recommender with a polished Streamlit UI.
"""

import re
import warnings

import streamlit as st

from recommender import get_engine

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CineScope — Movie Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
CSS = """
<style>
:root {
    --bg: #0b0f1a;
    --bg-2: #111827;
    --card: #1b2333;
    --card-hover: #232e45;
    --accent: #f5b301;
    --accent-2: #f97316;
    --text: #f3f4f6;
    --muted: #9aa4b8;
    --border: #283247;
}

.stApp {
    background: linear-gradient(160deg, #0b0f1a 0%, #131a2b 100%);
    color: var(--text);
}

[data-testid="stHeader"] { background: transparent; }

.block-container { padding-top: 2rem; max-width: 1200px; }

/* Hero */
.hero {
    text-align: center;
    padding: 1.2rem 0 0.6rem 0;
}
.hero h1 {
    font-size: 3rem;
    font-weight: 800;
    margin: 0;
    background: linear-gradient(90deg, #f5b301, #f97316);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -1px;
}
.hero p {
    color: var(--muted);
    font-size: 1.05rem;
    margin-top: 0.4rem;
}

/* Section heading */
.section-title {
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--text);
    margin: 1.6rem 0 0.8rem 0;
    border-left: 4px solid var(--accent);
    padding-left: 0.7rem;
}

/* Movie card */
.movie-card {
    background: var(--card);
    border-radius: 14px;
    border: 1px solid var(--border);
    overflow: hidden;
    transition: transform .15s ease, box-shadow .15s ease;
    height: 100%;
    display: flex;
    flex-direction: column;
}
.movie-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 28px rgba(0,0,0,.45);
}
.movie-card img {
    width: 100%;
    aspect-ratio: 2 / 3;
    object-fit: cover;
    display: block;
}
.movie-body {
    padding: 0.7rem 0.9rem 0.9rem 0.9rem;
    flex: 1;
}
.movie-title {
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--text);
    line-height: 1.3;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.movie-genres {
    color: var(--muted);
    font-size: 0.78rem;
    margin-top: 0.35rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem;
}
.chip {
    background: #2c3a54;
    color: #cdd7e6;
    border-radius: 999px;
    padding: 0.1rem 0.5rem;
    font-size: 0.7rem;
}
.movie-score {
    margin-top: 0.5rem;
    font-size: 0.78rem;
    color: var(--accent);
    font-weight: 600;
}

/* Placeholder poster when no image */
.poster-placeholder {
    width: 100%;
    aspect-ratio: 2 / 3;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(160deg, #2c3a54, #1b2333);
    color: var(--muted);
    font-size: 2rem;
    font-weight: 800;
    text-align: center;
    padding: 1rem;
    box-sizing: border-box;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--bg-2);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
    color: var(--accent);
}

/* Widgets */
.stButton > button {
    background: linear-gradient(90deg, #f5b301, #f97316);
    color: #111;
    font-weight: 700;
    border: none;
    border-radius: 10px;
    padding: 0.55rem 1.4rem;
    transition: opacity .15s ease;
}
.stButton > button:hover {
    opacity: 0.88;
    color: #111;
}
div[data-baseweb="select"] > div {
    background: var(--card);
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 10px;
}

footer { visibility: hidden; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
PLACEHOLDER_COLORS = [
    "#2c3a54", "#3b4a63", "#4a3b63", "#633b4a", "#3b6359",
    "#5a4a3b", "#354563", "#63452c",
]


def poster_slug(title):
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip().replace(" ", "-") or "movie"


def poster_url(movie_id):
    if movie_id:
        return (
            "https://image.tmdb.org/t/p/w500/"
            f"{movie_id}.png"
        )
    return None


def render_poster(movie_id, title, key_prefix):
    """Show a poster image with an elegant offline placeholder fallback."""
    parts = f"""
    <div class="poster-placeholder" style="background:linear-gradient(160deg, {PLACEHOLDER_COLORS[hash(key_prefix) % len(PLACEHOLDER_COLORS)]}, #1b2333);">
        {title[:26].upper()}
    </div>
    """
    return parts


def card_html(item, idx):
    title = item["title"]
    genres = engine.genres_of(title)
    genre_chips = "".join(f'<span class="chip">{g}</span>' for g in genres[:4])
    score = item.get("score")
    score_html = (
        f'<div class="movie-score">★ Match {score:.0%}</div>'
        if score is not None
        else "<div class=\"movie-score\">Recommended</div>"
    )
    pid = item.get("id")
    img_html = poster_slug(title)
    return f"""
    <div class="movie-card">
        {render_poster(pid, title, key_prefix=f"{idx}_{title}")}
        <div class="movie-body">
            <div class="movie-title">{title}</div>
            <div class="movie-genres">{genre_chips}</div>
            {score_html}
        </div>
    </div>
    """


def show_cards(results, cols=5):
    """Render result list as a responsive grid of cards."""
    rows = (len(results) + cols - 1) // cols
    for row in range(rows):
        cards = st.columns(cols)
        for col in range(cols):
            idx = row * cols + col
            if idx < len(results):
                with cards[col]:
                    st.markdown(
                        card_html(results[idx], idx),
                        unsafe_allow_html=True,
                    )


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading movie database…")
def load_engine():
    return get_engine()


try:
    engine = load_engine()
    ALL_GENRES = sorted(
        {
            g
            for title in engine.titles
            for g in engine.genres_of(title)
        }
    )
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>🎬 CineScope</h1>
        <p>Smart movie discovery powered by content-based filtering</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("## Control Panel")
MODE_LABELS = {
    "similar": "✨ Similar to a movie",
    "genre_similar": "🎭 Same favourites",
    "browse": "🧭 Browse by genre",
    "curated": "🌟 Curated picks",
}


def mode_description(mode):
    return {
        "similar": "Find movies closely related to the one you pick using content similarity.",
        "genre_similar": "Discover movies that share the same genres as your favourite.",
        "browse": "Explore popular titles across a genre of your choice.",
        "curated": "A hand-picked set of well-known crowd favourites.",
    }[mode]


mode = st.sidebar.radio("Recommendation mode", list(MODE_LABELS), format_func=MODE_LABELS.get)
count = st.sidebar.slider("Number of recommendations", 1, 10, 5)
st.sidebar.markdown(f"<small style='color:var(--muted)'>{mode_description(mode)}</small>",
                    unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown(
    "<small style='color:var(--muted)'>CineScope • offline content-based engine</small>",
    unsafe_allow_html=True,
)

st.markdown(f'<div class="section-title">{MODE_LABELS[mode]}</div>', unsafe_allow_html=True)

try:
    if mode == "similar":
        st.markdown(
            "<small style='color:var(--muted)'>Begin typing to search your movie library.</small>",
            unsafe_allow_html=True,
        )
        query = st.text_input("Search a movie", placeholder="e.g. Inception, Avatar, Titanic…")
        selected = None
        if query.strip():
            results = engine.search(query, limit=20)
            if results:
                selected = st.selectbox("Select a movie", results)
            else:
                st.info("No matches found. Try a different spelling.")
        if selected and st.button("Show recommendations", type="primary"):
            with st.spinner("Computing recommendations…"):
                recs = engine.by_similarity(selected, count)
            show_cards(recs)
        elif not selected:
            st.caption("Start typing above to pick a movie.")

    elif mode == "genre_similar":
        st.caption("Pick a favourite movie and get titles that share its genres.")
        query = st.text_input("Search a movie", placeholder="e.g. The Matrix, Gladiator…")
        selected = None
        if query.strip():
            results = engine.search(query, limit=20)
            if results:
                selected = st.selectbox("Select a movie", results)
            else:
                st.info("No matches found. Try a different spelling.")
        if selected and st.button("Show recommendations", type="primary"):
            with st.spinner("Finding same-genre titles…"):
                recs = engine.by_genre_similar(selected, count)
            show_cards(recs)
        elif not selected:
            st.caption("Start typing above to pick a movie.")

    elif mode == "browse":
        genre = st.selectbox("Choose a genre", ALL_GENRES)
        if st.button("Explore", type="primary"):
            with st.spinner("Gathering titles…"):
                recs = engine.by_genre(genre, count)
            show_cards(recs)

    elif mode == "curated":
        st.caption("Popular, broadly loved titles to get you started.")
        recs = engine.curated(count)
        show_cards(recs)

except Exception as exc:  # noqa: BLE001
    st.error(f"Something went wrong: {exc}")
