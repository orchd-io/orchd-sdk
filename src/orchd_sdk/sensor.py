# The MIT License (MIT)
# Copyright © 2022 <Mathias Santos de Brito>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import asyncio
import uuid
from abc import ABC, abstractmethod
from asyncio import Task

from orchd_sdk.reaction import global_reactions_event_bus, ReactionsEventBus

from orchd_sdk.models import Event, SensorTemplate, Sensor


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
        self.id = str(uuid.uuid4())

    @abstractmethod
    async def emit_event(self, event: Event):
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
        self.id = str(uuid.uuid4())
        self.sensor_template = sensor_template
        self.communicator = communicator
        self.sensing_interval = sensor_template.sensing_interval or sensing_interval
        self._state = SensorState.READY
        self._start_task: Task = None
        self._events_counter = -1
        self._events_forwarded = -1
        self._events_discarded = -1

    @abstractmethod
    async def sense(self):
        """
        Sensor function to be called in order to sense an external event.

        It will be called in loop while the sensor is running.
        """

    async def _start(self):
        while self.state == SensorState.RUNNING:
            await self.sense()
            await asyncio.sleep(self.sensing_interval)
        self._start_task.set_result(None)

    def start(self):
        """
        Prepares the sensor and starts it.

        The basic implementation calls the sense method in a loop, it will
        stop when the state of the sensor changes to SensorState.STOPPED

        This is a basic implementation and can be overridden if necessary.
        """
        self.state = SensorState.RUNNING
        self._start_task = asyncio.get_event_loop().create_task(self._start())

    async def stop(self):
        """
        Stops the sensor main loop and release resources.

        This is a basic implementation and can be overridden if necessary.
        """
        self.state = SensorState.STOPPED

    def status(self):
        return Sensor(
            id=self.id, template=self.sensor_template, status=self._state,
            events_count=self._events_counter, events_forwarded=self._events_forwarded,
            events_discarded=self._events_discarded
        )

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state


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
        await self.communicator.emit_event(
            Event(event_name='io.orchd.events.system.Test', data={'dummy': 'data'})
        )


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
