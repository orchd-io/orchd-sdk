import asyncio
from unittest.mock import AsyncMock

import pytest

from orchd_sdk.reaction import ReactionsEventBus
from orchd_sdk.sensor import DummySensor, LocalCommunicator, SensorState


class TestSensor:

    @pytest.mark.asyncio
    async def test_sensor_lifecycle(self):
        """
        Test the lifecycle of a sensor.

        A sensor can be in three different states:
        - READY, if the object is initialized correctly.
        - RUNNING, when start is called
        - STOPPED, when stop is called

        Here we test the behavior of the sensor stat after calling each
        of the methods that must impact its value.
        :return:
        """
        sensor = DummySensor(DummySensor.template, LocalCommunicator())
        assert sensor.state == SensorState.READY

        sensor.start()
        await asyncio.sleep(0.1)  # Gives the chance to start execute...
        assert sensor.state == SensorState.RUNNING

        await sensor.stop()
        assert sensor.state == SensorState.STOPPED

    @pytest.mark.asyncio
    async def test_sense_awaited(self):
        """
        Test if start calls the sense method.

        When start is called, it will call sense in a loop in a frequency
        defined when creating the sensor (this value defaults to 0). This
        tests ensures that sense is called (awaited since it is a coroutine)
        """
        sensor = DummySensor(DummySensor.template, LocalCommunicator())
        sense_mock = AsyncMock()
        sensor.sense = sense_mock

        sensor.start()
        await asyncio.sleep(0.1)  # Give a chance for start to be called
        await sensor.stop()
        sense_mock.assert_awaited()


class TestLocalCommunicator:

    def test___init__(self):
        """
        Tests if the ReactionEventBus is handled correctly.

        LocalCommunicators will use the global event bus it none is given.
        """
        from orchd_sdk.sensor import global_reactions_event_bus

        communicator1 = LocalCommunicator()
        assert communicator1.event_bus is global_reactions_event_bus

        bus = ReactionsEventBus()
        communicator2 = LocalCommunicator(event_bus=bus)
        assert communicator2.event_bus is bus
