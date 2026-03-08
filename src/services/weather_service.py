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
import datetime

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

    def _get_coordinates(self, destination: str, country: str):
        query = f"{destination}, {country}"
        location = self.geocode(query, language="en")

        if not location:
            logger.error(f"Location not found for {query}")
            return None, None

        logger.info(f"Location found: {location.latitude}, {location.longitude}")
        return location.latitude, location.longitude

    def _call_api(self, lat: float, lon: float, params: dict):
        base_params = {
            "latitude": lat,
            "longitude": lon,
        }

        full_params = {**base_params, **params}

        try:
            responses = self.client.weather_api(self.url, params=full_params)
            return responses[0]

        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return None

    def _format_weather_keys(self, weather_dict: dict) -> dict:
        key_mapping = {
            "temperature": "temperature (°C)",
            "wind_speed": "wind_speed (km/h)",
        }

        formatted = {}

        for key, value in weather_dict.items():
            new_key = key_mapping.get(key, key)
            formatted[new_key] = value

        return formatted

    def get_weather(self, destination: str, country: str):

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
            "destination": destination,
            "country": country,
            "latitude": lat,
            "longitude": lon,
            "temperature": current.Variables(0).Value(),
            "wind_speed": current.Variables(1).Value(),
        }

        result_formattted = self._format_weather_keys(result)
        logger.info(f"Current weather: {result}")
        logger.info(f"Current weather formatted: {result_formattted}")
        return result_formattted

    def plot_forecast(self, destination: str, country: str):

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
                "date": dates,
                "temperature": temperature,
                "wind_speed": wind_speed,
                "precipitation_probability": precipitation_prob,
            }
        )

        logger.info(
            f"Forecast and past 3-days weather dataframe with shape: {df.shape}"
        )

        # Create Figures
        now = pd.Timestamp.utcnow()
        past_df = df[df["date"] <= now]  # Past Data
        future_df = df[df["date"] > now]  # Forecast Data

        fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

        # Temperature
        axes[0].plot(
            past_df["date"], past_df["temperature"], label="Past", linestyle="-"
        )
        axes[0].plot(
            future_df["date"],
            future_df["temperature"],
            label="Forecast",
            linestyle="--",
        )
        axes[0].axvline(now, linestyle=":", linewidth=2, label="Today", color="red")
        axes[0].set_title(f"Temperature - {destination}")
        axes[0].set_ylabel("°C")
        axes[0].legend()
        axes[0].grid(True)

        # Wind
        axes[1].plot(past_df["date"], past_df["wind_speed"], linestyle="-")
        axes[1].plot(future_df["date"], future_df["wind_speed"], linestyle="--")
        axes[1].axvline(now, linestyle=":", linewidth=2, color="red")
        axes[1].set_title("Wind Speed")
        axes[1].set_ylabel("km/h")
        axes[1].grid(True)

        # Precipitation Probability
        axes[2].plot(
            past_df["date"], past_df["precipitation_probability"], linestyle="-"
        )
        axes[2].plot(
            future_df["date"], future_df["precipitation_probability"], linestyle="--"
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
