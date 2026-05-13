import requests

# ============================================================
# CONFIGURATION
# ============================================================
API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0ZWQ2YTAzZTM4ZGNlY2U4Y2U3YTFjMDg1ZjcxYWVlNiIsIm5iZiI6MTc3NjY5MDUxMS4zNDcwMDAxLCJzdWIiOiI2OWU2MjU0ZjU4YjA3NTdmZmIwNjQ1MGQiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.3qIsPo80AXWJ14TwTm4a8ScO6sfTioNT_EiOVDoWhcc"

BASE_URL = "https://api.themoviedb.org/3"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "accept": "application/json"
}

MOVIE_MOOD_TO_GENRES = {
    "happy":       [35, 10402, 10751],
    "sad":         [35, 10749],
    "excited":     [18, 28, 53],
    "relaxed":     [16, 99, 10749, 10751],
    "scared":      [27, 80, 9648],
    "bored":       [28, 12, 878, 10752],
    "romantic":    [18, 10749],
    "family night":[16, 35, 10751],
    "movie night": [35, 53],
    "rainy day":   [18, 99, 878, 9648],
}
TV_MOOD_TO_GENRES = {
    "happy":       [35, 10751],
    "sad":         [35, 18],
    "excited":     [10759, 9648],
    "relaxed":     [16, 99, 10751],
    "scared":      [9648, 80],
    "bored":       [10759, 10765, 10768],
    "romantic":    [18],
    "family night":[16, 35, 10751],
    "movie night": [35, 9648],
    "rainy day":   [18, 99, 9648],
}

MOVIE_GENRES = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 18: "Drama", 27: "Horror", 9648: "Mystery",
    10749: "Romance", 878: "Science Fiction", 53: "Thriller",
    10751: "Family", 10402: "Music", 99: "Documentary", 10752: "War",
}
TV_GENRES = {
    10759: "Action & Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
    10762: "Kids", 9648: "Mystery", 10763: "News", 10764: "Reality",
    10765: "Sci-Fi & Fantasy", 10766: "Soap", 10767: "Talk",
    10768: "War & Politics",
}


class Movie:
    def __init__(self, title, genre_ids, rating, overview, release_date, runtime=None, platforms=None):
        self.title = title
        self.genre_ids = genre_ids
        self.rating = rating
        self.overview = overview
        self.release_date = release_date
        self.runtime = runtime
        self.platforms = platforms if platforms is not None else []


class User:
    def __init__(self, name, mood, content_type, max_time, preferred_genres, release_period):
        self.name = name
        self.mood = mood
        self.content_type = content_type
        self.max_time = max_time
        self.preferred_genres = preferred_genres
        self.release_period = release_period
        self.watched_movies = []


class RecommendationEngine:
    def __init__(self, user):
        self.user = user

    def get_genre_ids(self):
        if self.user.preferred_genres:
            return self.user.preferred_genres
        if self.user.content_type == "movie":
            return MOVIE_MOOD_TO_GENRES.get(self.user.mood, [])
        return TV_MOOD_TO_GENRES.get(self.user.mood, [])

    def get_platforms(self, movie_id, content_type):
        url = (
            f"{BASE_URL}/movie/{movie_id}/watch/providers"
            if content_type == "movie"
            else f"{BASE_URL}/tv/{movie_id}/watch/providers"
        )
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            data = response.json()
        except Exception:
            return []
        pt_data = data.get("results", {}).get("PT", {})
        return [p["provider_name"] for p in pt_data.get("flatrate", [])]

    def gather_recommendations(self):
        genre_ids = self.get_genre_ids()
        genre_string = "|".join(str(g) for g in genre_ids)

        endpoint = (
            f"{BASE_URL}/discover/movie"
            if self.user.content_type == "movie"
            else f"{BASE_URL}/discover/tv"
        )

        parameters = {
            "with_genres": genre_string,
            "sort_by": "popularity.desc",
            "vote_count.gte": 100,
            "with_original_language": "en",
        }

        if self.user.max_time is not None:
            parameters["with_runtime.lte"] = self.user.max_time

        if self.user.content_type == "movie":
            if self.user.release_period == "old":
                parameters["primary_release_date.lte"] = "1999-12-31"
            elif self.user.release_period == "new":
                parameters["primary_release_date.gte"] = "2000-01-01"
        else:
            if self.user.release_period == "old":
                parameters["first_air_date.lte"] = "1999-12-31"
            elif self.user.release_period == "new":
                parameters["first_air_date.gte"] = "2000-01-01"

        try:
            response = requests.get(endpoint, headers=HEADERS, params=parameters)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.ConnectionError:
            return [], "Could not connect to TMDB. Check your internet connection."
        except requests.exceptions.HTTPError as e:
            return [], f"API Error: {e}"

        results = data.get("results", [])

        if not results:
            if "with_runtime.lte" in parameters:
                del parameters["with_runtime.lte"]
            else:
                for key in ["primary_release_date.lte", "primary_release_date.gte",
                            "first_air_date.lte", "first_air_date.gte"]:
                    parameters.pop(key, None)
            response = requests.get(endpoint, headers=HEADERS, params=parameters)
            results = response.json().get("results", [])

        if not results:
            return [], "No results found. Try different preferences."

        movies = []
        for item in results:
            if self.user.content_type == "movie":
                title = item.get("title") or "Unknown"
                release_date = item.get("release_date") or "N/A"
            else:
                title = item.get("name") or "Unknown"
                release_date = item.get("first_air_date") or "N/A"

            overview = item.get("overview") or "No description available."
            platforms = self.get_platforms(item["id"], self.user.content_type)

            movies.append(Movie(
                title,
                item.get("genre_ids", []),
                item.get("vote_average", 0),
                overview,
                release_date,
                platforms=platforms,
            ))

        return movies, None

    def filter_by_rating(self, movies, min_rating=6.0):
        filtered = [m for m in movies if m.rating >= min_rating]
        return filtered if filtered else movies

    def rank_movies(self, movies):
        return sorted(movies, key=lambda m: m.rating, reverse=True)

    def generate_recommendations(self):
        all_movies, error = self.gather_recommendations()
        if error:
            return [], [], error

        filtered = self.filter_by_rating(all_movies)
        ranked = self.rank_movies(filtered)

        unwatched = [m for m in ranked if m.title.lower() not in self.user.watched_movies]
        watched = [m for m in ranked if m.title.lower() in self.user.watched_movies]

        return unwatched[:10], watched, None
