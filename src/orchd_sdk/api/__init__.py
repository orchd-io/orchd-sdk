import json
from abc import abstractmethod, ABC

import aiohttp
import pydantic
from pydantic import parse_obj_as, BaseModel, Field

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
        event = json.loads(await self.__anext__())
        return parse_obj_as(Event, event)

    async def close(self):
        await self.response.release()


class OrchdAbstractClientAdpter(ABC):
    @abstractmethod
    def _url(self, path: str):
        pass

    @abstractmethod
    async def get(self, path: str):
        pass

    @abstractmethod
    async def post(self, path: str, data: dict):
        pass

    @abstractmethod
    async def delete(self, path: str):
        pass

    @abstractmethod
    async def put(self, path: str, data: dict):
        pass

    @abstractmethod
    async def stream(self, path: str):
        pass


class OrchdHttpClientAdapter(OrchdAbstractClientAdpter):

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


class OrchdZeroMQMessage(BaseModel):
    path: Field(str, description='The path of the request, to the operation')
    parameters: Field(dict, description='The parameters of the request')
    payload: Field(dict, description='The payload of the request')


class OrchdZeroMQAdpater(OrchdAbstractClientAdpter):

    def _url(self, path: str):
        pass

    async def get(self, path: str):
        pass

    async def post(self, path: str, data: dict):
        pass

    async def delete(self, path: str):
        pass

    async def put(self, path: str, data: dict):
        pass

    async def stream(self, path: str):
        pass


def adpter_factory(adpter_type: str, host: str, port: int, token: str = None):
    if adpter_type == 'http':
        return OrchdHttpClientAdapter(host, port, token)
    else:
        raise NotImplementedError
