import uuid

import pytest
import pytest_asyncio

from orchd_sdk.api import OrchdAgentClient
from orchd_sdk.models import ReactionTemplate, SinkTemplate, SensorTemplate
from orchd_sdk.reaction import DummyReaction
from orchd_sdk.sensor import DummySensor
from orchd_sdk.sink import DummySink


@pytest_asyncio.fixture(scope='function')
async def client() -> OrchdAgentClient:
    cli = OrchdAgentClient('127.0.0.1', 8000)
    yield cli
    await cli.close()


@pytest.fixture(scope='function')
def reaction_template():
    template = ReactionTemplate(**DummyReaction.template.dict())
    template.id = str(uuid.uuid4())
    return template


@pytest.fixture(scope='function')
def sink_template():
    sink = SinkTemplate(**DummySink.template.dict())
    sink.id = str(uuid.uuid4())
    return sink


@pytest.fixture(scope='function')
def sensor_template():
    sensor_template = SensorTemplate(**DummySensor.template.dict())
    sensor_template.id = str(uuid.uuid4())
    return sensor_template


@pytest_asyncio.fixture(scope='function')
async def added_sensor(client, sensor_template):
    # Add a sensor to the client and remove it aftewards
    # This removal is important since the Dummy Sensor keeps propagating events.
    template = await client.sensors.add_sensor_template(sensor_template)
    sensor = await client.sensors.add_sensor(sensor_template.id)
    yield sensor
    await client.sensors.remove_sensor(sensor.id)
