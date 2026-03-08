import json

from src.db.excel_db import ExcelDestinationsDB
from src.services.weather_service import WeatherService
from src.utils.logger_config import logger


def tool_list_destinations(db: ExcelDestinationsDB) -> str:
    """Return a list of available destinations."""
    logger.info("Listing destinations...")
    return json.dumps({"destinations": db.list_destinations()})


def tool_get_destination_info(db: ExcelDestinationsDB, destination: str) -> str:
    """Return structured info about a destination."""
    infos = db.get_destination(destination)
    logger.info(f"Destination {destination} infos found: {infos}")
    return json.dumps({"destination": destination, "found": bool(infos), "info": infos})


def tool_search_destinations_by_keyword(db: ExcelDestinationsDB, keyword: str) -> str:
    """Search destinations by keyword (e.g., beaches, museums)."""
    results = db.search_by_keyword(keyword)
    logger.info(f"Keyword {keyword} -> results: {results}.")
    return json.dumps({"keyword": keyword, "results": results})


def tool_recommend_destinations_by_season(
    db: ExcelDestinationsDB, season_query: str
) -> str:
    """Recommend destinations that match a season query (e.g., 'April', 'November')."""
    results = db.recommend_by_season(season_query)
    logger.info(f"Season query {season_query} -> results: {results}")
    return json.dumps({"season_query": season_query, "results": results})


weather_service = WeatherService()


def tool_get_live_weather(db: ExcelDestinationsDB, destination: str):
    infos = db.get_destination(destination)
    logger.info(f"Destination {destination} -> infos: {infos}.")

    if not infos:
        logger.error(f"Destination {destination} infos not found in database")
        return json.dumps({"error": "Destination not found in database"})

    country = infos.get("country")
    logger.info(f"Found country: {country} for destination {destination}.")

    weather = weather_service.get_weather(destination, country)
    logger.info(f"Weather data for {destination}: {weather}")

    return json.dumps(weather)
