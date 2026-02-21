import json

from src.agents.tools.get_prices import get_ticket_price


class TravelAssistant:
    def __init__(self, llm, system_prompt: str):
        self.llm = llm
        self.system_prompt = system_prompt
        self._define_tools()

    def _define_tools(self):
        price_function = {
            "name": "get_ticket_price",
            "description": "Get the price of a return ticket to the destination city. ONLY call this tool if the user explicitly asks for ticket price or cost.'",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination_city": {
                        "type": "string",
                        "description": "The city that the customer wants to travel to",
                    },
                },
                "required": ["destination_city"],
                "additionalProperties": False,
            },
        }
        self.tools = [{"type": "function", "function": price_function}]

    def _handle_tool_call(self, tool_calls):
        tool_call = tool_calls[0]
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        if name == "get_ticket_price":
            city = args.get("destination_city")
            result = get_ticket_price(city)
            return {"role": "tool", "tool_call_id": tool_call.id, "content": result}

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
        if response.finish_reason == "tool_calls":
            message = response.message
            tool_output = self._handle_tool_call(tool_calls=response.tool_calls)
            msgs.append(message)
            msgs.append(tool_output)

            final_response = self.llm.generate(messages=msgs, tools=None)

            return final_response.content

        else:
            return response.content
