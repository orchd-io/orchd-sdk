import json

import aiohttp
from pydantic import parse_obj_as, TypeAdapter

from orchd_sdk.api.events import EventClient
from orchd_sdk.api.reactions import ReactionClient
from orchd_sdk.api.sensors import SensorClient
from orchd_sdk.api.sinks import SinkClient
from orchd_sdk.errors import handle_http_errors
from orchd_sdk.models import Event


class HTTPEventStream:
    def __init__(self, response):
        self.response = response
        self._stream = response.content

    async def __aiter__(self):
        return self

    async def __anext__(self):
        chunk = await self._stream.read(4096)
        return chunk.decode('utf-8')

    async def next(self):
        adapter = TypeAdapter(Event)
        event = json.loads(await self.__anext__())
        return adapter.validate_python(event)

    async def close(self):
        await self.response.release()


class OrchdAgentClient:

    def __init__(self, host: str, port: int, token: str = None):
        self._host = host
        self._port = port
        self._token = token
        self._session = aiohttp.ClientSession()
        if token:
            self._session.headers.update(
                {'Authorization': f'Bearer {self._token}'})

        self.reactions = ReactionClient(self)
        self.sinks = SinkClient(self)
        self.sensors = SensorClient(self)
        self.events = EventClient(self)

    def _url(self, path: str):
        return f'http://{self._host}:{self._port}/orchd/v1{path}'

    async def get(self, path: str):
        async with self._session.get(self._url(path)) as response:
            handle_http_errors(response)
            return await response.json()

    async def post(self, path: str, data: dict):
        async with self._session.post(self._url(path), json=data) as response:
            handle_http_errors(response)
            return await response.json()

    async def delete(self, path: str):
        async with self._session.delete(self._url(path)) as response:
            handle_http_errors(response)
            return await response.json()

    async def put(self, path: str, data: dict):
        async with self._session.put(self._url(path), json=data) as response:
            handle_http_errors(response)
            return await response.json()

    async def stream(self, path: str):
        response = await self._session.get(self._url(path))
        handle_http_errors(response)
        return HTTPEventStream(response)

    async def close(self):
        await self._session.close()

