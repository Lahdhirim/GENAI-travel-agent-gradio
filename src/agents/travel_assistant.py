class TravelAssistant:
    def __init__(self, llm, system_prompt: str):
        self.llm = llm
        self.system_prompt = system_prompt

    def chat(self, message, history):

        msgs = [{"role": "system", "content": self.system_prompt}]
        msgs.extend(
            {"role": h["role"], "content": h["content"]} for h in (history or [])
        )
        msgs.append({"role": "user", "content": message})

        return self.llm.generate(msgs)
