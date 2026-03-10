import requests_cache
from retry_requests import retry
import openmeteo_requests
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
from PIL import Image
import numpy as np
from typing import Tuple, Dict, Any

from src.utils.logger_config import logger
from src.utils.schema import WeatherSchema


class WeatherService:
    """Service responsible for geocoding locations and retrieving weather data."""

    def __init__(self):
        # Geocoder
        self.geolocator = Nominatim(user_agent="travel_assistant")
        self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=1)

        # Open-Meteo client with caching and retries
        cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
        retry_session = retry(cache_session, retries=3, backoff_factor=0.2)
        self.client = openmeteo_requests.Client(session=retry_session)

        self.url = "https://api.open-meteo.com/v1/forecast"

    def _get_coordinates(self, destination: str, country: str) -> Tuple[float, float]:
        """Resolve latitude and longitude for a destination."""

        query = f"{destination}, {country}"
        location = self.geocode(query, language="en")

        if not location:
            logger.error(f"Location not found for {query}")
            return None, None

        logger.info(f"Location found: {location.latitude}, {location.longitude}")
        return location.latitude, location.longitude

    def _call_api(self, lat: float, lon: float, params: dict):
        """Call the Open-Meteo API with provided parameters."""

        base_params = {
            WeatherSchema.LATITUDE: lat,
            WeatherSchema.LONGITUDE: lon,
        }

        full_params = {**base_params, **params}

        try:
            responses = self.client.weather_api(self.url, params=full_params)
            return responses[0]

        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return None

    def _format_weather_keys(self, weather_dict: dict) -> Dict[str, Any]:
        """Format output keys with readable units."""

        key_mapping = {
            WeatherSchema.TEMPERATURE: WeatherSchema.TEMPERATURE_C,
            WeatherSchema.WIND_SPEED: WeatherSchema.WIND_SPEED_KM_H,
        }

        formatted = {}

        for key, value in weather_dict.items():
            new_key = key_mapping.get(key, key)
            formatted[new_key] = value

        return formatted

    def get_weather(self, destination: str, country: str) -> Dict[str, Any]:
        """Retrieve current weather conditions for a destination."""

        lat, lon = self._get_coordinates(destination, country)
        if lat is None or lon is None:
            return {"error": "Location not found"}

        # Get Current weather
        response = self._call_api(
            lat, lon, {"current": ["temperature_2m", "wind_speed_10m"]}
        )

        if not response:
            return {"error": "Failed to fetch weather data"}

        current = response.Current()
        result = {
            WeatherSchema.DESTINATION: destination,
            WeatherSchema.COUNTRY: country,
            WeatherSchema.LATITUDE: lat,
            WeatherSchema.LONGITUDE: lon,
            WeatherSchema.TEMPERATURE: current.Variables(0).Value(),
            WeatherSchema.WIND_SPEED: current.Variables(1).Value(),
        }

        result_formattted = self._format_weather_keys(result)
        logger.info(f"Current weather: {result}")
        logger.info(f"Current weather formatted: {result_formattted}")
        return result_formattted

    def plot_forecast(self, destination: str, country: str):
        """Generate a past + forecast weather plot and return it as an image array."""

        lat, lon = self._get_coordinates(destination, country)
        if lat is None or lon is None:
            return None

        # Get forecast and past weather
        response = self._call_api(
            lat,
            lon,
            {
                "hourly": [
                    "temperature_2m",
                    "wind_speed_10m",
                    "precipitation_probability",
                ],
                "past_days": 3,
                "forecast_days": 3,
                "timezone": "auto",
            },
        )

        if not response:
            return None

        hourly = response.Hourly()
        dates = pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )

        temperature = hourly.Variables(0).ValuesAsNumpy()
        wind_speed = hourly.Variables(1).ValuesAsNumpy()
        precipitation_prob = hourly.Variables(2).ValuesAsNumpy()

        df = pd.DataFrame(
            {
                WeatherSchema.DATE: dates,
                WeatherSchema.TEMPERATURE: temperature,
                WeatherSchema.WIND_SPEED: wind_speed,
                WeatherSchema.PRECIPITATION_PROB: precipitation_prob,
            }
        )

        logger.info(
            f"Forecast and past 3-days weather dataframe with shape: {df.shape}"
        )

        # Create Figures
        now = pd.Timestamp.utcnow()
        past_df = df[df[WeatherSchema.DATE] <= now]  # Past Data
        future_df = df[df[WeatherSchema.DATE] > now]  # Forecast Data

        fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

        # Temperature
        axes[0].plot(
            past_df[WeatherSchema.DATE],
            past_df[WeatherSchema.TEMPERATURE],
            label="Past",
            linestyle="-",
        )
        axes[0].plot(
            future_df[WeatherSchema.DATE],
            future_df[WeatherSchema.TEMPERATURE],
            label="Forecast",
            linestyle="--",
        )
        axes[0].axvline(now, linestyle=":", linewidth=2, label="Today", color="red")
        axes[0].set_title(f"Temperature - {destination}")
        axes[0].set_ylabel("°C")
        axes[0].legend()
        axes[0].grid(True)

        # Wind
        axes[1].plot(
            past_df[WeatherSchema.DATE],
            past_df[WeatherSchema.WIND_SPEED],
            linestyle="-",
        )
        axes[1].plot(
            future_df[WeatherSchema.DATE],
            future_df[WeatherSchema.WIND_SPEED],
            linestyle="--",
        )
        axes[1].axvline(now, linestyle=":", linewidth=2, color="red")
        axes[1].set_title("Wind Speed")
        axes[1].set_ylabel("km/h")
        axes[1].grid(True)

        # Precipitation Probability
        axes[2].plot(
            past_df[WeatherSchema.DATE],
            past_df[WeatherSchema.PRECIPITATION_PROB],
            linestyle="-",
        )
        axes[2].plot(
            future_df[WeatherSchema.DATE],
            future_df[WeatherSchema.PRECIPITATION_PROB],
            linestyle="--",
        )
        axes[2].axvline(now, linestyle=":", linewidth=2, color="red")
        axes[2].set_title("Precipitation Probability")
        axes[2].set_ylabel("%")
        axes[2].grid(True)

        axes[2].xaxis.set_major_locator(mdates.AutoDateLocator())
        axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))

        plt.xticks(rotation=45)
        plt.tight_layout()

        # Convert figure to image for Gradio
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        img = Image.open(buf)
        img_array = np.array(img)
        plt.close(fig)

        return img_array
