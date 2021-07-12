import asyncio
from abc import ABC, abstractmethod

from orchd_sdk.event import global_reactions_event_bus, ReactionsEventBus

from orchd_sdk.models import Event, SensorTemplate


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
    def emit_event(self, event: Event):
        """
        Emits the event in the orchd agent's Reactor.
        :param event: Event to be emitted
        """

    @abstractmethod
    def close(self):
        """
        Closes connections and releases resources.
        """

    @abstractmethod
    async def authenticate(self):
        """
        Authenticates the sensor against the Orchd Agent.
        """


class SensorState:
    READY = (2, 'READY')
    RUNNING = (3, 'RUNNING')
    STOPPED = (4, 'STOPPED')


class AbstractSensor(ABC):
    """
    Base class to be used to implement Sensors to be used in orchd.

    Sensors need to implement the logic that will detect external events
    and inject it in Orchd. To inject the event they will use the Communicator.
    """

    @abstractmethod
    def __init__(self, sensor_template: SensorTemplate,
                 communicator: AbstractCommunicator,
                 sensing_interval=0):
        self.sensor_template = sensor_template
        self.communicator = communicator
        self.sensing_interval = sensing_interval
        self.state = SensorState.READY

    @abstractmethod
    async def sense(self):
        """
        Sensor function to be called in order to sense an external event.

        It will be called in loop while the sensor is running.
        """

    async def start(self):
        """
        Prepares the sensor and starts it.

        The basic implementation calls the sense method in a loop, it will
        stop when the state of the sensor changes to SensorState.STOPPED

        This is a basic implementation and can be overridden if necessary.
        """
        self.state = SensorState.RUNNING
        while self.state == SensorState.RUNNING:
            await self.sense()
            await asyncio.sleep(self.sensing_interval)

    async def stop(self):
        """
        Stops the sensor main loop and release resources.

        This is a basic implementation and can be overridden if necessary.
        """
        self.state = SensorState.STOPPED


class DummySensor(AbstractSensor):
    """
    Dummy sensor that emits io.orchd.events.system.Test events.
    """
    def __init__(self, sensor_template,  communicator: AbstractCommunicator):
        super().__init__(sensor_template, communicator)
        self.state = SensorState.READY

    template = SensorTemplate(
        name='io.orchd.sensor_template.DummySensor',
        description='A dummy Sensor to be used for testing purposes',
        version='1.0',
        sensor='orchd_sdk.sensor.DummySensor',
        communicator='orchd_sdk.sensor.LocalCommunicator',
        parameters={'some': 'data'},
        sensing_interval=0
    )

    async def sense(self):
        await asyncio.sleep(1)
        self.communicator.emit_event(Event(event_name='io.orchd.events.system.Test',
                                           data={'dummy': 'data'}))


class LocalCommunicator(AbstractCommunicator):
    """
    Object Message Communicator for emitting events.

    This communicator emits events by invoking the given ReactionsEventBus
    that is used by the Reactor. This communicator do not requires authentication
    since it is part of the system. It is intended to provide more performance.

    If no ReactionsBusEvent object is given the default one is used instead.

    It is recommended that this communicator to be Ued by trusted sensors.
    """

    def __init__(self, event_bus: ReactionsEventBus = None):
        super().__init__()
        self.event_bus = event_bus or global_reactions_event_bus

    async def emit_event(self, event: Event):
        """
        Emits an event using the global ReactionsEventBus
        :param event: Event to emit.
        """
        self.event_bus.event(event)

    async def authenticate(self):
        """
        no-op since local communicator do not need to authenticate.
        """
        pass

    def close(self):
        """
        no-op since it is a local communicator and do not uses additions
        resources/connections.
        """