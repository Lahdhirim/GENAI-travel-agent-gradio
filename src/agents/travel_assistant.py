import json

from src.utils.logger_config import logger
from src.agents.tools.destinations_infos import (
    tool_list_destinations,
    tool_get_destination_info,
    tool_search_destinations_by_keyword,
    tool_recommend_destinations_by_season,
    tool_get_live_weather,
)
from src.db.excel_db import ExcelDestinationsDB
from src.services.weather_service import WeatherService
from src.agents.tools.mcp_flight_client import MCPFlightClient

# [LOW]: add Schema


class TravelAssistant:
    def __init__(self, llm, system_prompt: str, destinations_excel_path: str):
        self.llm = llm
        self.system_prompt = system_prompt
        self.db = ExcelDestinationsDB(destinations_excel_path)
        self.weather_service = WeatherService()
        self.flight_client = MCPFlightClient()
        # [MEDIUM]: add tools dynamically from config file
        self.tool_registry = {
            "list_destinations": lambda **_: tool_list_destinations(self.db),
            "get_destination_info": lambda destination, **_: tool_get_destination_info(
                self.db, destination
            ),
            "search_destinations_by_keyword": lambda keyword, **_: tool_search_destinations_by_keyword(
                self.db, keyword
            ),
            "recommend_destinations_by_season": lambda season_query, **_: tool_recommend_destinations_by_season(
                self.db, season_query
            ),
            "get_live_weather": lambda destination, **_: tool_get_live_weather(
                self.db, self.weather_service, destination
            ),
        }
        self._define_tools()

    def _define_tools(self):
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "list_destinations",
                    "description": "List available destinations in the internal database. Call only if the user asks what destinations are available.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_destination_info",
                    "description": "Get destination information from the internal database (country, keywords, best_season). Call when the user asks about a destination.",
                    "parameters": {
                        "type": "object",
                        "properties": {"destination": {"type": "string"}},
                        "required": ["destination"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_destinations_by_keyword",
                    "description": "Search destinations by a keyword like 'beaches' or 'museums'. Call when user asks for destinations matching a theme.",
                    "parameters": {
                        "type": "object",
                        "properties": {"keyword": {"type": "string"}},
                        "required": ["keyword"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "recommend_destinations_by_season",
                    "description": "Recommend destinations by season query (e.g., 'April', 'November', 'March–May'). Call when user asks where to go in a specific period.",
                    "parameters": {
                        "type": "object",
                        "properties": {"season_query": {"type": "string"}},
                        "required": ["season_query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_live_weather",
                    "description": "Get current live weather for a destination. Call when user asks about current weather or temperature.",
                    "parameters": {
                        "type": "object",
                        "properties": {"destination": {"type": "string"}},
                        "required": ["destination"],
                    },
                },
            },
        ]

        # Add MCP Server Tools dynamically
        for mcp_tool in self.flight_client.list_tools():
            self.tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": mcp_tool["name"],
                        "description": mcp_tool.get("description", ""),
                        "parameters": mcp_tool.get(
                            "inputSchema", {"type": "object", "properties": {}}
                        ),
                    },
                }
            )
            self.tool_registry[mcp_tool["name"]] = lambda _tool=mcp_tool[
                "name"
            ], **args: self.flight_client._call_tool(_tool, args)

    def _handle_tool_call(self, tool_calls):
        tool_call = tool_calls[0]
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        if name not in self.tool_registry:
            logger.error(f"Unknown tool: {name}")
            return (
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": f"Unknown tool: {name}",
                },
                None,
            )

        logger.info(f"Calling tool: {name} with args: {args}")
        result_text, fig = self.tool_registry[name](**args)

        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": str(result_text),
        }, fig

    def chat(self, message, history) -> str:
        logger.info(f"User message: {message}")
        fig = None

        # System prompt
        msgs = [{"role": "system", "content": self.system_prompt}]
        # Add chat history
        msgs.extend(
            {"role": h["role"], "content": h["content"]} for h in (history or [])
        )
        # User prompt
        msgs.append({"role": "user", "content": message})

        response = self.llm.generate(messages=msgs, tools=self.tools)
        logger.info(f"Assistant response: {response.content}")

        # Handle tool calls
        while response.finish_reason == "tool_calls":
            logger.info("Handling tool calls...")
            assistant_message = response.message
            tool_output, tool_fig = self._handle_tool_call(
                tool_calls=response.tool_calls
            )

            if tool_fig is not None:
                fig = tool_fig

            msgs.append(assistant_message)
            msgs.append(tool_output)
            logger.info(f"Assistant tool output: {tool_output}")

            response = self.llm.generate(messages=msgs, tools=self.tools)
            logger.info(
                f"Assistant response after handling tool calls: {response.content}"
            )

        return response.content, fig
