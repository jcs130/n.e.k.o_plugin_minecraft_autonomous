"""Optional decision-model adapter, distinct from N.E.K.O's main persona and voice."""

from .autonomy.planner import decision


class NekoPlanner:
    def __init__(self, gateway, max_output_tokens):
        self.gateway, self.max_output_tokens = gateway, max_output_tokens
        self.client = None

    async def decide(self, messages, tools):
        if self.client is None:
            self.client = await self.gateway.get_client()
        response = await self.client.chat.completions.create(
            model="decision", messages=messages, tools=tools, parallel_tool_calls=False,
            max_completion_tokens=self.max_output_tokens,
        )
        choice = response.choices[0]
        if choice.finish_reason not in {"stop", "tool_calls"}:
            raise ValueError("brain_response_incomplete")
        return decision(choice.message.model_dump(exclude_none=True))

    async def aclose(self):
        await self.gateway.aclose()
