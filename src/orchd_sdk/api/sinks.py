from typing import List

from pydantic import parse_obj_as, TypeAdapter

from orchd_sdk.models import SinkTemplate

SINK_TEMPLATES_BASE_ROUTE = '/sink_templates'


class SinkClient:
    def __init__(self, orchd_agent_client):
        self.client = orchd_agent_client

    async def add_sink_template(self, template: SinkTemplate) -> SinkTemplate:
        response = await self.client.post(SINK_TEMPLATES_BASE_ROUTE, template.model_dump())
        return SinkTemplate(**response)

    async def get_sink_templates(self):
        adapter = TypeAdapter(List[SinkTemplate])
        response = await self.client.get(SINK_TEMPLATES_BASE_ROUTE)
        return adapter.validate_python(response)

    async def get_sink_template(self, template_id: str) -> SinkTemplate:
        response = await self.client.get(f'{SINK_TEMPLATES_BASE_ROUTE}/{template_id}/')
        return SinkTemplate(**response)

    async def remove_sink_template(self, template_id: str) -> str:
        response = await self.client.delete(f'{SINK_TEMPLATES_BASE_ROUTE}/{template_id}/')
        return response
