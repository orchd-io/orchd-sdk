from abc import ABC, abstractmethod
from event import global_reactions_event_bus
from orchd_sdk.models import Event


class SensorError(Exception):
    pass


class AbstractCommunicator(ABC):

    @abstractmethod
    def emit_event(self, event_name, data):
        pass


class AbstractSensor(ABC):

    def __init__(self, communicator: AbstractCommunicator):
        self.communicator = communicator

    @abstractmethod
    async def sense(self):
        pass


class LocalCommunicator(AbstractCommunicator):

    def __init__(self):
        if not global_reactions_event_bus:
            raise SensorError()

    async def emit_event(self, event_name, data):
        global_reactions_event_bus.event(Event(event_name=event_name,
                                               data=data))
