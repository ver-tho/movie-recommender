# Movie & TV Recommender

A mood-based movie and TV show recommender built with Streamlit and the TMDB API.

## Features

- Login / account creation
- Mood-based recommendations (10 moods)
- Genre selection (up to 2) or mood-based defaults
- Watch party mode — each person picks a genre
- Runtime filter
- Era filter (before/after 2000)
- Streaming platform availability (Portugal region)
- Watched list that persists across sessions

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub (public)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo and set **Main file path** to `app.py`
4. Click Deploy

## Project structure

```
app.py          # Streamlit UI and page routing
models.py       # TMDB API calls, Movie / User / RecommendationEngine classes
auth.py         # Account creation, login, watched-list persistence
requirements.txt
.gitignore
```

## Data source

[The Movie Database (TMDB)](https://www.themoviedb.org/) — free API.
