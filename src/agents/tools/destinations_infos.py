import json
from src.db.excel_db import ExcelDestinationsDB


def tool_list_destinations(db: ExcelDestinationsDB) -> str:
    """Return a list of available destinations."""
    return json.dumps({"destinations": db.list_destinations()})


def tool_get_destination_info(db: ExcelDestinationsDB, destination: str) -> str:
    """Return structured info about a destination."""
    info = db.get_destination(destination)
    return json.dumps({"destination": destination, "found": bool(info), "info": info})


def tool_search_destinations_by_keyword(db: ExcelDestinationsDB, keyword: str) -> str:
    """Search destinations by keyword (e.g., beaches, museums)."""
    results = db.search_by_keyword(keyword)
    return json.dumps({"keyword": keyword, "results": results})


def tool_recommend_destinations_by_season(
    db: ExcelDestinationsDB, season_query: str
) -> str:
    """Recommend destinations that match a season query (e.g., 'April', 'November')."""
    results = db.recommend_by_season(season_query)
    return json.dumps({"season_query": season_query, "results": results})
