import streamlit as st
from models import RecommendationEngine, User, MOVIE_GENRES, TV_GENRES
from auth import create_account, login, save_watched_movies, load_watched_movies

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="🎬 CineMatch",
    page_icon="🎬",
    layout="centered",
)

# ─────────────────────────────────────────────
# Global styling & background
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* Cinematic background */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460);
    min-height: 100vh;
}
[data-testid="stHeader"] { background: transparent; }

/* Toolbar icons (share, etc.) — force white */
[data-testid="stToolbar"] button svg,
[data-testid="stToolbar"] button,
[data-testid="stDecoration"] { color: #ffffff !important; fill: #ffffff !important; }
header button svg { fill: #ffffff !important; }

/* Make ALL text white/light */
html, body, [class*="css"], p, span, label, div,
[data-testid="stMarkdownContainer"] p,
[data-testid="stText"] {
    color: #f0f0f0 !important;
}

/* Headings bright white */
h1, h2, h3, h4 { color: #ffffff !important; }

/* Inputs: WHITE background, BLACK text — fully readable */
input, textarea,
[data-testid="stTextInput"] input,
[data-testid="stTextInput"] textarea {
    background: #ffffff !important;
    color: #111111 !important;
    border: 1px solid rgba(255,255,255,0.4) !important;
    border-radius: 8px !important;
}
input::placeholder,
textarea::placeholder { color: #777777 !important; }

/* Multiselect input area */
[data-testid="stMultiSelect"] input { color: #111111 !important; }
[data-testid="stMultiSelect"] > div { background: #ffffff !important; color: #111111 !important; }
[data-testid="stMultiSelect"] span { color: #111111 !important; }

/* Selectbox */
[data-testid="stSelectbox"] select,
[data-testid="stSelectbox"] > div { background: #ffffff !important; color: #111111 !important; }

/* Tabs */
[data-testid="stTabs"] button { color: #cccccc !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color: #ffffff !important; }

/* Radio & checkbox labels */
[data-testid="stRadio"] label,
[data-testid="stCheckbox"] label { color: #f0f0f0 !important; }

/* Expander headers */
[data-testid="stExpander"] summary {
    color: #ffffff !important;
    background: rgba(255,255,255,0.06);
    border-radius: 10px;
}
[data-testid="stExpander"] {
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 12px;
    margin-bottom: 8px;
}

/* ALL buttons: white background, black text by default */
.stButton > button {
    background: #ffffff !important;
    color: #111111 !important;
    border: 1px solid rgba(255,255,255,0.4) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

/* ALL buttons hover: dark blue background, white text */
.stButton > button:hover {
    background: #0f3460 !important;
    color: #ffffff !important;
    border-color: #0f3460 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(15,52,96,0.5) !important;
}

/* Primary button (Get recommendations): red, always white text */
.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #e94560, #c0392b) !important;
    color: #ffffff !important;
    border: none !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(90deg, #c0392b, #a93226) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 20px rgba(233,69,96,0.5) !important;
}

/* Info / warning banners */
[data-testid="stAlert"] { color: #f0f0f0 !important; }

/* Divider */
hr { border-color: rgba(255,255,255,0.15) !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Session state defaults
# ─────────────────────────────────────────────
for key, default in {
    "username": None,
    "watched": [],
    "recommendations": None,
    "watched_matches": None,
    "error": None,
    "page": "auth",      # auth | prefs | results
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ─────────────────────────────────────────────
# Helper: movie card
# ─────────────────────────────────────────────
def movie_card(movie, idx, show_watch_button=True):
    already_watched = movie.title.lower() in st.session_state["watched"]
    label = f"#{idx}  {movie.title}  ·  ⭐ {movie.rating:.1f}/10"
    if already_watched:
        label += "  ✅"

    with st.expander(label):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Released:** {movie.release_date}")
            if movie.platforms:
                st.markdown(f"**Streaming on:** {', '.join(movie.platforms)}")
            else:
                st.markdown("*Not available on major streaming platforms in your region.*")
            st.markdown(movie.overview)
        with col2:
            if show_watch_button and not already_watched:
                if st.button("Mark as watched ✅", key=f"watch_{movie.title}_{idx}"):
                    st.session_state["watched"].append(movie.title.lower())
                    save_watched_movies(st.session_state["username"], st.session_state["watched"])
                    st.rerun()
            elif already_watched:
                st.success("Already watched!")


# ─────────────────────────────────────────────
# PAGE: Auth (login / create account)
# ─────────────────────────────────────────────
def page_auth():
    st.markdown("""
        <h1 style='text-align:center; font-size:3rem; margin-bottom:0;'>🎬 CineMatch</h1>
        <p style='text-align:center; color:#aaa; font-size:1.1rem; margin-top:4px;'>
            Mood-based movie & TV recommendations
        </p>
    """, unsafe_allow_html=True)
    st.divider()
    st.info("⚠️ Accounts are session-only — you'll need to create a new account each visit.", icon="ℹ️")
    st.divider()

    tab_login, tab_create = st.tabs(["Login", "Create account"])

    with tab_login:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", use_container_width=True):
            ok, msg = login(username.strip(), password.strip())
            if ok:
                st.session_state["username"] = username.strip()
                st.session_state["watched"] = load_watched_movies(username.strip())
                st.session_state["page"] = "prefs"
                st.rerun()
            else:
                st.error(msg)

    with tab_create:
        new_user = st.text_input("Choose a username", key="reg_user")
        new_pass = st.text_input("Choose a password", type="password", key="reg_pass")
        if st.button("Create account", use_container_width=True):
            ok, msg = create_account(new_user.strip(), new_pass.strip())
            if ok:
                st.success(msg + " You can now log in.")
            else:
                st.error(msg)


# ─────────────────────────────────────────────
# PAGE: Preferences
# ─────────────────────────────────────────────
def page_prefs():
    st.title(f"Hello, {st.session_state['username']}! 👋")
    st.markdown("Tell us what you're in the mood for.")
    st.divider()

    # ── Mood ──
    mood_options = [
        "happy", "sad", "excited", "relaxed", "scared",
        "bored", "romantic", "family night", "movie night", "rainy day",
    ]
    mood = st.radio(
        "How are you feeling?",
        mood_options,
        index=None,
        horizontal=True,
        format_func=lambda m: m.capitalize(),
    )

    st.divider()

    # ── Content type ──
    content_type = st.radio(
        "What do you want to watch?",
        ["movie", "tv"],
        index=None,
        horizontal=True,
        format_func=lambda x: "🎬 Movie" if x == "movie" else "📺 TV Show",
    )

    # ── Release period ──
    period_map = {"Before 2000": "old", "After 2000": "new", "No preference": "any"}
    period_label = st.radio(
        "Era preference",
        list(period_map.keys()),
        index=None,
        horizontal=True,
    )
    release_period = period_map[period_label] if period_label else "any"

    st.divider()

    # ── Runtime ──
    has_limit = st.checkbox("Set a maximum runtime / episode length")
    max_time = None
    if has_limit:
        max_time = st.slider(
            "Maximum minutes",
            min_value=20,
            max_value=240,
            value=120,
            step=5,
        )

    st.divider()

    # ── Watch party ──
    party_mode = st.checkbox("🎉 Watch party mode (multiple people)")
    preferred_genres = []

    genre_map = MOVIE_GENRES if content_type != "tv" else TV_GENRES
    genre_name_to_id = {v: k for k, v in genre_map.items()}
    genre_names = sorted(genre_name_to_id.keys())

    if party_mode:
        n_people = st.number_input("How many people are watching?", min_value=2, max_value=10, value=2, step=1)
        st.markdown("Each person picks one genre:")
        for i in range(int(n_people)):
            pick = st.selectbox(f"Person #{i + 1}", genre_names, key=f"party_{i}")
            gid = genre_name_to_id[pick]
            if gid not in preferred_genres:
                preferred_genres.append(gid)
    else:
        picks = st.multiselect(
            "Preferred genres (up to 2 — leave empty to use mood-based genres)",
            genre_names,
            max_selections=2,
        )
        preferred_genres = [genre_name_to_id[p] for p in picks]

    st.divider()

    if st.button("🎯 Get recommendations", use_container_width=True, type="primary"):
        if not mood:
            st.warning("Please select a mood first.")
        elif not content_type:
            st.warning("Please select Movie or TV Show.")
        else:
            user = User(
                name=st.session_state["username"],
                mood=mood,
                content_type=content_type,
                max_time=max_time,
                preferred_genres=preferred_genres,
                release_period=release_period,
            )
            user.watched_movies = st.session_state["watched"]

            with st.spinner("Fetching recommendations from TMDB…"):
                engine = RecommendationEngine(user)
                recs, watched_matches, error = engine.generate_recommendations()

            if error:
                st.error(error)
            else:
                st.session_state["recommendations"] = recs
                st.session_state["watched_matches"] = watched_matches
                st.session_state["mood"] = mood
                st.session_state["page"] = "results"
                st.rerun()

    st.divider()
    if st.button("Logout", use_container_width=True):
        for key in ["username", "watched", "recommendations", "watched_matches", "page"]:
            st.session_state[key] = None if key == "username" else ([] if key == "watched" else "auth")
        st.session_state["page"] = "auth"
        st.rerun()


# ─────────────────────────────────────────────
# PAGE: Results
# ─────────────────────────────────────────────
def page_results():
    recs = st.session_state.get("recommendations", [])
    watched_matches = st.session_state.get("watched_matches", [])
    mood = st.session_state.get("mood", "")

    st.title(f"Top picks for you 🎬")
    st.markdown(f"**Mood:** {mood.capitalize()}  ·  **User:** {st.session_state['username']}")
    st.divider()

    if not recs:
        st.warning("No recommendations found. Try different preferences.")
    else:
        for i, movie in enumerate(recs[:5], 1):
            movie_card(movie, i)

        if len(recs) > 5:
            st.divider()
            with st.expander("Show 5 more recommendations"):
                for i, movie in enumerate(recs[5:10], 6):
                    movie_card(movie, i)

    if watched_matches:
        st.divider()
        st.markdown("### You've already watched these — but they match your mood!")
        for movie in watched_matches:
            movie_card(movie, "✅", show_watch_button=False)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Search again", use_container_width=True, type="primary"):
            st.session_state["page"] = "prefs"
            st.session_state["recommendations"] = None
            st.rerun()
    with col2:
        if st.button("Logout", use_container_width=True):
            for key in ["username", "watched", "recommendations", "watched_matches"]:
                st.session_state[key] = None if key == "username" else []
            st.session_state["page"] = "auth"
            st.rerun()


# ─────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────
page = st.session_state["page"]

if page == "auth" or not st.session_state["username"]:
    page_auth()
elif page == "prefs":
    page_prefs()
elif page == "results":
    page_results()
