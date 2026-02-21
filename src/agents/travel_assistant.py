class TravelAssistant:
    def __init__(self, llm, system_prompt: str):
        self.llm = llm
        self.system_prompt = system_prompt

    def chat(self, message, history):

        prompt = f"""
            {self.system_prompt}

            User:
            {message}

            Assistant:
            """
        return self.llm.generate(prompt)
