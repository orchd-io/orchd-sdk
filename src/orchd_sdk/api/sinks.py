from typing import List

from pydantic import parse_obj_as

from orchd_sdk.models import SinkTemplate

SINK_TEMPLATES_BASE_ROUTE = '/sink_templates'


class SinkClient:
    def __init__(self, orchd_agent_client):
        self.client = orchd_agent_client

    async def add_sink_template(self, template: SinkTemplate) -> SinkTemplate:
        response = await self.client.post(SINK_TEMPLATES_BASE_ROUTE, template.dict())
        return SinkTemplate(**response)

    async def get_sink_templates(self):
        response = await self.client.get(SINK_TEMPLATES_BASE_ROUTE)
        return parse_obj_as(List[SinkTemplate], response)

    async def get_sink_template(self, template_id: str) -> SinkTemplate:
        response = await self.client.get(f'{SINK_TEMPLATES_BASE_ROUTE}/{template_id}/')
        return SinkTemplate(**response)

    async def remove_sink_template(self, template_id: str) -> str:
        response = await self.client.delete(f'{SINK_TEMPLATES_BASE_ROUTE}/{template_id}/')
        return response
