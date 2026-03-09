import json
import os
from typing import Annotated, Dict, Any
from dotenv import load_dotenv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))
import requests
from mcp.server.fastmcp import FastMCP
from pydantic import Field

from src.utils.logger_config import mcp_logger

API_BASE_URL = "https://api.aviationstack.com/v1"

mcp = FastMCP("Aviation MCP Server", host="0.0.0.0", port=8001)

load_dotenv()

# Set up logging
with open("logs/mcp_server.log", "w") as log_file:
    pass
mcp_logger.info("Logging setup complete")


def _get_api_key() -> str:
    """Retrieve AviationStack API key from environment."""

    api_key = os.getenv("AVIATION_STACK_API_KEY")
    if not api_key:
        mcp_logger.error("AVIATION_STACK_API_KEY environment variable not set")
        raise ValueError("AVIATION_STACK_API_KEY not set")

    mcp_logger.info("AviationStack API key loaded successfully")
    return api_key


def fetch(endpoint: str, params: dict) -> Dict[str, Any]:
    """Call AviationStack API and return JSON response."""

    api_key = _get_api_key()

    mcp_logger.info(f"Calling AviationStack endpoint='{endpoint}' params={params}")

    try:
        response = requests.get(
            f"{API_BASE_URL}/{endpoint}",
            params={"access_key": api_key, **params},
            timeout=15,
        )
        mcp_logger.debug(f"AviationStack response status={response.status_code}")
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        mcp_logger.exception(f"AviationStack API request failed: {e}")
        return None


@mcp.tool(
    name="search_flights",
    description="Search scheduled flights between two airports using IATA codes (e.g., CDG to SFO). This calls an external MCP Aviation server.",
)
def search_flights(
    dep_iata: Annotated[
        str, Field(description="Departure Airport name (e.g., CDG for Paris)")
    ],
    arr_iata: Annotated[
        str, Field(description="Arrival Airport name (e.g., SFO for San Francisco)")
    ],
) -> str:
    """Search scheduled flights between two airports."""

    mcp_logger.info(f"Flight search requested: {dep_iata} -> {arr_iata}")

    data = fetch(
        "flights",
        {"dep_iata": dep_iata, "arr_iata": arr_iata, "flight_status": "scheduled"},
    )

    if data:
        flights = data.get("data", [])
        mcp_logger.info(f"AviationStack returned {len(flights)} flights")

        if flights:
            results = []
            for f in flights:
                results.append(
                    {
                        "flight_number": f.get("flight", {}).get("number"),
                        "date": f.get("flight_date"),
                        "airline_name": f.get("airline", {}).get("name"),
                    }
                )

            return json.dumps(results, indent=2)

        else:
            return json.dumps({"Message": "No scheduled flights found"})

    else:
        mcp_logger.warning("Flight API request failed, returning fallback message")
        return json.dumps(
            {
                "error": "Flight data unavailable",
                "message": "Unable to retrieve flight information at the moment.",
            }
        )


if __name__ == "__main__":
    """Start the MCP Aviation Flight Server."""
    mcp_logger.info("Starting MCP Aviation Flight Server on port 8001")
    mcp.run(transport="streamable-http")
