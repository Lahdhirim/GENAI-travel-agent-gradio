import requests
import json


class MCPFlightClient:
    def __init__(self, base_url="http://localhost:8001"):
        self.session_url = f"{base_url}/mcp"
        self.session = requests.Session()
        self.session_id = self._initialize()
        self._send_initialized_notification()

    def _initialize(self) -> str:
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
            raise RuntimeError(
                f"No session ID returned. Headers: {dict(response.headers)}"
            )

        return session_id

    def _send_initialized_notification(self):
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

    def list_tools(self) -> list[dict]:
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
        return data.get("result", {}).get("tools", [])

    def _parse_sse(self, raw_bytes: bytes) -> dict:
        text = raw_bytes.decode("utf-8")

        for line in text.splitlines():
            if line.startswith("data:"):
                json_str = line.replace("data:", "").strip()
                return json.loads(json_str)

        raise ValueError("No data line found in SSE response")

    def _call_tool(self, tool_name: str, arguments: dict):
        """Generic tool caller used by all public methods."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        try:
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
                return json.dumps(parsed_result, indent=2), None

            return json.dumps({"Message": "No response"}), None

        except Exception as e:
            return (
                json.dumps(
                    {
                        "Error": "Sorry, I'm not able to retrieve flight data for the moment"
                    }
                ),
                None,
            )

    def search_flights(self, dep_iata: str, arr_iata: str):
        return self._call_tool(
            "search_flights", {"dep_iata": dep_iata, "arr_iata": arr_iata}
        )
