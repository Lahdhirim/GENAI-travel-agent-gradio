import requests
import json
from typing import Tuple

from src.utils.logger_config import logger
from src.utils.schema import ToolsSchema


class MCPFlightClient:
    """Client responsible for communicating with the MCP flight server."""

    def __init__(self, base_url="http://localhost:8001"):
        self.session_url = f"{base_url}/mcp"
        self.session = requests.Session()
        self.session_id = self._initialize()
        self._send_initialized_notification()

    def _initialize(self) -> str:
        """Initialize an MCP session and return the session ID."""

        payload = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "flight-client", "version": "1.0"},
            },
        }
        response = self.session.post(
            self.session_url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            timeout=10,
        )

        session_id = response.headers.get("mcp-session-id")
        if not session_id:
            logger.error("MCP server did not return a session ID")
            raise RuntimeError(
                f"No session ID returned. Headers: {dict(response.headers)}"
            )

        logger.info(f"MCP session initialized with session_id={session_id}")
        return session_id

    def _send_initialized_notification(self):
        """Notify the MCP server that the client finished initialization."""

        payload = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }

        self.session.post(
            self.session_url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": self.session_id,
            },
            timeout=5,
        )

        logger.info("MCP initialized notification sent")

    def list_tools(self) -> list[dict]:
        """Retrieve the list of tools exposed by the MCP server."""

        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }
        response = self.session.post(
            self.session_url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": self.session_id,
            },
            timeout=10,
        )
        data = self._parse_sse(response.content)
        tools = data.get("result", {}).get("tools", [])

        logger.info(f"MCP server returned {len(tools)} tools")
        return tools

    def _parse_sse(self, raw_bytes: bytes) -> dict:
        """Parse SSE response and extract JSON payload."""

        text = raw_bytes.decode("utf-8")

        for line in text.splitlines():
            if line.startswith("data:"):
                json_str = line.replace("data:", "").strip()
                return json.loads(json_str)

        logger.error("Failed to parse SSE response: no data line found")
        raise ValueError("No data line found in SSE response")

    def _call_tool(self, tool_name: str, arguments: dict) -> Tuple[str, None]:
        """Generic tool caller used by all public methods."""

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        try:
            logger.info(f"Calling MCP tool: {tool_name} with args={arguments}")

            response = self.session.post(
                self.session_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "mcp-session-id": self.session_id,
                },
                timeout=20,
            )
            data = self._parse_sse(response.content)
            content = data.get("result", {}).get("content", [])

            if content:
                text_result = content[0].get("text", "{}")
                parsed_result = json.loads(text_result)

                logger.info(f"MCP tool '{tool_name}' returned results: {parsed_result}")

                return json.dumps(parsed_result, indent=2), None

            logger.warning(f"MCP tool '{tool_name}' returned empty response")
            return json.dumps({"Message": "No response"}), None

        except Exception as e:
            logger.exception(f"MCP tool '{tool_name}' failed: {e}")
            return (
                json.dumps(
                    {
                        "Error": "Sorry, I'm not able to retrieve flight data for the moment"
                    }
                ),
                None,
            )

    def search_flights(self, dep_iata: str, arr_iata: str):
        """Search flights between two airports."""

        return self._call_tool(
            ToolsSchema.SEARCH_FLIGHTS, {"dep_iata": dep_iata, "arr_iata": arr_iata}
        )
