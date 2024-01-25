from typing import Dict

from orchd_sdk.models import Event

EVENTS_BASE_ROUTE = '/events/'


class EventClient:

    def __init__(self, orch_client):
        self.orchd_client = orch_client

    async def propagate(self, event_name: str, event_data: Dict):
        await self.orchd_client.post(EVENTS_BASE_ROUTE,
                                     data=Event(event_name=event_name,
                                                data=event_data).model_dump())

    async def event_stream(self):
        return await self.orchd_client.stream(f'{EVENTS_BASE_ROUTE}event_stream')
