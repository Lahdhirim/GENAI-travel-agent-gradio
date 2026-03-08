import json
import os
from typing import Annotated
from dotenv import load_dotenv

import requests
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# [MEDIUM]: Add logger for server

API_BASE_URL = "https://api.aviationstack.com/v1"

mcp = FastMCP("Aviation MCP Server", host="0.0.0.0", port=8001)

load_dotenv()


def _get_api_key():
    api_key = os.getenv("AVIATION_STACK_API_KEY")
    if not api_key:
        raise ValueError("AVIATION_STACK_API_KEY not set")
    return api_key


def fetch(endpoint: str, params: dict):
    api_key = _get_api_key()
    response = requests.get(
        f"{API_BASE_URL}/{endpoint}",
        params={"access_key": api_key, **params},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


@mcp.tool(name="search_flights")
def search_flights(
    dep_iata: Annotated[
        str, Field(description="Departure Airport name (e.g., CDG for Paris)")
    ],
    arr_iata: Annotated[
        str, Field(description="Arrival Airport name (e.g., SFO for San Francisco)")
    ],
) -> str:

    data = fetch(
        "flights",
        {"dep_iata": dep_iata, "arr_iata": arr_iata, "flight_status": "scheduled"},
    )

    flights = data.get("data", [])

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


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
