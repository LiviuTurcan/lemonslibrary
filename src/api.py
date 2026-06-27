import datetime
import os
import requests
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()


class IGDBClient:

    def __init__(self):
        self.client_id = os.getenv("TWITCH_CLIENT_ID")
        self.client_secret = os.getenv("TWITCH_CLIENT_SECRET")
        self.access_token = None
        self.token_expiry = None

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Twitch credentials missing! Please check your .env file."
            )

    def _get_access_token(self):
        """Requests an OAuth token from Twitch or returns the cached token if it's still valid."""
        # If token exists and is not expired, reuse it
        if (
            self.access_token
            and self.token_expiry
            and datetime.datetime.now() < self.token_expiry
        ):
            return self.access_token

        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }

        response = requests.post(url, params=params)
        response.raise_for_status()
        data = response.json()

        self.access_token = data["access_token"]
        expires_in = data["expires_in"]

        # Cache token expiry, subtracting a 60-second safety buffer
        self.token_expiry = datetime.datetime.now() + datetime.timedelta(
            seconds=expires_in - 60
        )
        return self.access_token

    def search_game(self, query):
        """Searches IGDB for a game by title, reranks them by string similarity, and returns top results."""
        try:
            token = self._get_access_token()
        except Exception as e:
            print(f"Authentication failed: {e}")
            return []

        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {token}",
            "Content-Type": "text/plain",
        }

        # Request 10 candidates so we have enough variety to sort locally
        query_body = f'search "{query}"; fields name, first_release_date, cover.url, involved_companies.company.name, involved_companies.developer, genres.name, summary; limit 10;'

        url = "https://api.igdb.com/v4/games"

        try:
            response = requests.post(url, headers=headers, data=query_body)
            response.raise_for_status()
            games = response.json()
        except Exception as e:
            print(f"IGDB API query failed: {e}")
            return []

        parsed_games = []
        for game in games:
            # 1. Parse Release Date
            release_timestamp = game.get("first_release_date")
            release_date = "Unknown"
            if release_timestamp:
                try:
                    release_date = datetime.date.fromtimestamp(
                        release_timestamp
                    ).strftime("%Y-%m-%d")
                except (ValueError, OSError):
                    pass

            # 2. Parse Cover
            cover_data = game.get("cover", {})
            raw_cover_url = cover_data.get("url")
            cover_url = None
            if raw_cover_url:
                cover_url = "https:" + raw_cover_url.replace(
                    "t_thumb", "t_cover_big"
                )

            # 3. Parse Developers
            developers = []
            for company_info in game.get("involved_companies", []):
                if company_info.get("developer", False):
                    name = company_info.get("company", {}).get("name")
                    if name:
                        developers.append(name)
            developer_str = ", ".join(developers) if developers else "Unknown"

            # 4. Parse Genres
            genres = [
                genre.get("name")
                for genre in game.get("genres", [])
                if genre.get("name")
            ]
            genre_str = ", ".join(genres) if genres else "Unknown"

            # 5. Parse Description
            description = game.get("summary", "No description available.")

            parsed_games.append(
                {
                    "title": game.get("name"),
                    "release_date": release_date,
                    "cover_url": cover_url,
                    "developer": developer_str,
                    "genre": genre_str,
                    "description": description,
                }
            )

        # Local Reranking: Sort games based on how closely their titles match the query
        def calculate_relevance(game_item):
            title_lower = game_item["title"].lower()
            query_lower = query.lower()

            if title_lower == query_lower:
                return 0  # Exact match (highest priority)
            elif title_lower.startswith(query_lower):
                return 1  # Starts with query
            elif query_lower in title_lower:
                return 2  # Contains query
            return 3  # Broad match

        parsed_games.sort(key=calculate_relevance)

        # Return only the top 5 most relevant results
        return parsed_games[:5]