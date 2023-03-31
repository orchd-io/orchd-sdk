import pytest

from orchd_sdk.errors import NotFoundError, InvalidRequestError
from orchd_sdk.sensor import SensorState


@pytest.mark.asyncio
async def test_get_sensor_templates(client, sensor_template):
    sensors = await client.sensors.get_sensor_templates()
    assert type(sensors) == list


@pytest.mark.asyncio
async def test_get_sensor_template(client, sensor_template):
    template = await client.sensors.add_sensor_template(sensor_template)
    response = await client.sensors.get_sensor_template(template.id)
    assert response == template


@pytest.mark.asyncio
async def test_get_nonexistent_sensor_template(client):
    with pytest.raises(NotFoundError):
        await client.sensors.get_sensor_template('invalid-id')


@pytest.mark.asyncio
async def test_add_sensor_template(client, sensor_template):
    currenr_len = len(await client.sensors.get_sensor_templates())
    await client.sensors.add_sensor_template(sensor_template)

    new_len = len(await client.sensors.get_sensor_templates())
    assert new_len == currenr_len + 1


@pytest.mark.asyncio
async def test_add_invalid_sensor_template(client, sensor_template):
    sensor_template.name = None
    with pytest.raises(InvalidRequestError):
        await client.sensors.add_sensor_template(sensor_template)


@pytest.mark.asyncio
async def test_remove_sensor_template(client, sensor_template):
    template = await client.sensors.add_sensor_template(sensor_template)
    response = await client.sensors.remove_sensor_template(template.id)
    assert response == template.id


@pytest.mark.asyncio
async def test_remove_nonexistent_sensor_template(client):
    with pytest.raises(NotFoundError):
        await client.sensors.remove_sensor_template('invalid-id')


@pytest.mark.asyncio
async def test_get_sensors(client, sensor_template):
    sensors = await client.sensors.get_sensors()
    assert type(sensors) == list


@pytest.mark.asyncio
async def test_get_sensor(client, sensor_template, added_sensor):
    response = await client.sensors.get_sensor(added_sensor.id)
    assert response == added_sensor


@pytest.mark.asyncio
async def test_add_sensor(client, sensor_template):
    template = await client.sensors.add_sensor_template(sensor_template)
    response = await client.sensors.add_sensor(template.id)
    assert response.template.id == template.id

    await client.sensors.remove_sensor(response.id)


@pytest.mark.asyncio
async def test_stop_sensor(client, sensor_template, added_sensor):
    assert added_sensor.status == SensorState.RUNNING

    await client.sensors.stop_sensor(added_sensor.id)
    updated_sensor = await client.sensors.get_sensor(added_sensor.id)

    assert updated_sensor.status == SensorState.STOPPED


@pytest.mark.asyncio
async def test_start_sensor(client, sensor_template, added_sensor):
    await client.sensors.stop_sensor(added_sensor.id)
    updated_sensor = await client.sensors.get_sensor(added_sensor.id)
    assert updated_sensor.status == SensorState.STOPPED

    await client.sensors.start_sensor(added_sensor.id)
    updated_sensor = await client.sensors.get_sensor(added_sensor.id)

    assert updated_sensor.status == SensorState.RUNNING


@pytest.mark.asyncio
async def test_remove_sensor(client, sensor_template):
    template = await client.sensors.add_sensor_template(sensor_template)
    sensor = await client.sensors.add_sensor(template.id)

    response = await client.sensors.remove_sensor(sensor.id)
    assert response == sensor.id

    with pytest.raises(NotFoundError):
        await client.sensors.get_sensor(sensor.id)

