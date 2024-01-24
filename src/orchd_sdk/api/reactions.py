from typing import List

from pydantic import TypeAdapter

from orchd_sdk.models import ReactionInfo, ReactionTemplate, Ref


class ReactionClient:

    def __init__(self, orchd_client):
        self.orchd_client = orchd_client

    async def get_reactions(self) -> List[ReactionInfo]:
        reactions = await self.orchd_client.get('/reactions')
        adapter = TypeAdapter(List[ReactionInfo])
        return adapter.validate_python(reactions)

    async def get_reaction(self, reaction_id: str) -> ReactionInfo:
        reaction = await self.orchd_client.get(f'/reactions/{reaction_id}')
        return ReactionInfo(**reaction)

    async def add_reaction(self, template_id: str) -> ReactionInfo:
        response = await self.orchd_client.post('/reactions', Ref(id=template_id).model_dump())
        return ReactionInfo(**response)

    async def remove_reaction(self, reaction_id: str) -> str:
        response = await self.orchd_client.delete(f'/reactions/{reaction_id}')
        return response

    async def get_reaction_templates(self) -> List[ReactionTemplate]:
        templates = await self.orchd_client.get('/reactions/templates/')
        adapter = TypeAdapter(List[ReactionTemplate])
        return adapter.validate_python(templates)

    async def get_reaction_template(self, template_id: str) -> ReactionTemplate:
        template = await self.orchd_client.get(f'/reactions/templates/{template_id}')
        return ReactionTemplate(**template)

    async def add_reaction_template(self, template: ReactionTemplate) -> ReactionTemplate:
        response = await self.orchd_client.post('/reactions/templates/', template.model_dump())
        return ReactionTemplate(**response)

    async def remove_reaction_template(self, template_id: str) -> str:
        response = await self.orchd_client.delete(f'/reactions/templates/{template_id}/')
        return response

    async def add_sink_to_reaction(self, reaction_id: str, template_id: str) -> str:
        response = await self.orchd_client.post(f'/reactions/{reaction_id}/sinks',
                                                Ref(id=template_id).model_dump())
        return response

    async def remove_sink_from_reaction(self, reaction_id: str, sink_id: str) -> str:
        response = await self.orchd_client.delete(f'/reactions/{reaction_id}/sinks/{sink_id}')
        return response
