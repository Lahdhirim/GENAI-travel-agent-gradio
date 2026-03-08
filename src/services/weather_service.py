import requests_cache
from retry_requests import retry
import openmeteo_requests
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from src.utils.logger_config import logger


class WeatherService:
    def __init__(self):
        # Geocoder
        self.geolocator = Nominatim(user_agent="travel_assistant")
        self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=1)

        # Open-Meteo
        cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
        retry_session = retry(cache_session, retries=3, backoff_factor=0.2)
        self.client = openmeteo_requests.Client(session=retry_session)

        self.url = "https://api.open-meteo.com/v1/forecast"

    def get_weather(self, destination: str, country: str):

        query = f"{destination}, {country}"
        location = self.geocode(query, language="en")

        if not location:
            logger.error(f"Location not found for {query}")
            return {"error": "Location not found"}

        lat = location.latitude
        lon = location.longitude
        logger.info(f"Location found: {lat}, {lon}")

        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ["temperature_2m", "wind_speed_10m", "precipitation"],
        }

        try:
            responses = self.client.weather_api(self.url, params=params)
            response = responses[0]

            current = response.Current()
            result = {
                "destination": destination,
                "country": country,
                "latitude": lat,
                "longitude": lon,
                "temperature": current.Variables(0).Value(),
                "wind_speed": current.Variables(1).Value(),
                "precipitation": current.Variables(2).Value(),
            }

            logger.info(f"Current weather: {result}")

            return result

        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return {"error": "Failed to fetch weather data"}
