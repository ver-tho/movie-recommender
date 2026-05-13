import streamlit as st
from models import RecommendationEngine, User, MOVIE_GENRES, TV_GENRES
from auth import create_account, login, save_watched_movies, load_watched_movies

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Movie & TV Recommender",
    page_icon="🎬",
    layout="centered",
)

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
    st.title("🎬 Movie & TV Recommender")
    st.markdown("Find something to watch based on your mood.")
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
        horizontal=True,
        format_func=lambda m: m.capitalize(),
    )

    st.divider()

    # ── Content type ──
    content_type = st.radio(
        "What do you want to watch?",
        ["movie", "tv"],
        horizontal=True,
        format_func=lambda x: "🎬 Movie" if x == "movie" else "📺 TV Show",
    )

    # ── Release period ──
    period_map = {"Before 2000": "old", "After 2000": "new", "No preference": "any"}
    period_label = st.radio(
        "Era preference",
        list(period_map.keys()),
        horizontal=True,
    )
    release_period = period_map[period_label]

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

    genre_map = MOVIE_GENRES if content_type == "movie" else TV_GENRES
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
