import json

from src.agents.tools.destinations_infos import (
    tool_list_destinations,
    tool_get_destination_info,
    tool_search_destinations_by_keyword,
    tool_recommend_destinations_by_season,
)
from src.db.excel_db import ExcelDestinationsDB


class TravelAssistant:
    def __init__(self, llm, system_prompt: str, destinations_excel_path: str):
        self.llm = llm
        self.system_prompt = system_prompt
        self.db = ExcelDestinationsDB(destinations_excel_path)
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
        ]

    def _handle_tool_call(self, tool_calls):
        tool_call = tool_calls[0]
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        if name not in self.tool_registry:
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": f"Unknown tool: {name}",
            }

        result = self.tool_registry[name](**args)

        return {"role": "tool", "tool_call_id": tool_call.id, "content": str(result)}

        # [MEDIUM]: add live weather retrieving tool

    def chat(self, message, history) -> str:

        # System prompt
        msgs = [{"role": "system", "content": self.system_prompt}]
        # Add chat history
        msgs.extend(
            {"role": h["role"], "content": h["content"]} for h in (history or [])
        )
        # User prompt
        msgs.append({"role": "user", "content": message})

        response = self.llm.generate(messages=msgs, tools=self.tools)

        # Handle tool calls
        while response.finish_reason == "tool_calls":
            message = response.message
            tool_output = self._handle_tool_call(tool_calls=response.tool_calls)
            msgs.append(message)
            msgs.append(tool_output)

            response = self.llm.generate(messages=msgs, tools=self.tools)

        return response.content
