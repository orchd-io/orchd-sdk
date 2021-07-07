from typing import Any
from abc import ABC, abstractmethod

from event import global_reactions_event_bus

from orchd_sdk.models import Event


class SensorError(Exception):
    """
    Exception raised by a Sensor for errors occurring in it.
    """
    pass


class AbstractCommunicator(ABC):
    """
    A communicator establishes a link to the Reactor to send events.

    A communicator abstracts the communication between the Sensor and Reactor.
    Different Communicators can be implemented and used by the Sensors. This
    design allows the creation of new forms of communication if needed.

    Communicators need to authenticate against the orchd agent to be allowed
    to emit events on it if communicating through the network.
    """

    def __init__(self):
        self._authenticated = False

    @abstractmethod
    def emit_event(self, event_name, data):
        """
        Emits the event in the orchd agent's Reactor.
        :param event_name: name of the event
        :param data: additional data related to the event.
        """
        pass

    @abstractmethod
    def authenticate(self):
        """
        Authenticates the sensor against the Orchd Agent.
        """
        pass


class AbstractSensor(ABC):
    """
    Base class to be used to implement Sensors to be used in orchd.

    Sensors need to implement the logic that will detect external events
    and inject it in Orchd. To inject the event they will use the Communicator.
    """

    def __init__(self, communicator: AbstractCommunicator,
                 sensor_template):
        self.sensor_template = sensor_template
        self.communicator = communicator

    @abstractmethod
    async def sense(self):
        """
        Starts the sensor main loop.
        """
        pass


class LocalCommunicator(AbstractCommunicator):
    """
    Object Message Communicator for emitting events.

    This communicator emits events by invoking the global ReactorEventBus
    that is used by the Reactor. This communicator do not requires authentication
    since it is part of the system. It is intended to provide more performance.

    It is recommended that this communicator to be Ued by trusted sensors.
    """

    def __init__(self):
        super().__init__()

    async def emit_event(self, event_name: str, data: Any):
        """
        Emits an event using the global ReactionsEventBus
        :param event_name: name of the event.
        :param data: additional data related to the event.
        """
        global_reactions_event_bus.event(Event(event_name=event_name,
                                               data=data))

    def authenticate(self):
        """
        no-op since local communicator do not need to authenticate.
        """
        pass
