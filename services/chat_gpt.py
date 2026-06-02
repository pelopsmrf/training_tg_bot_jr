from openai import AsyncOpenAI


class ChatGPTService:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def ask_gpt(self, system: str, question: str) -> str:
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": system
                },
                {
                    "role": "user", 
                    "content": question
                },
                ],
            max_tokens=1000,
            temperature=0.7,
        )
        return response.choices[0].message.content