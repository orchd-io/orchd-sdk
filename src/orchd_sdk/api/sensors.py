from typing import List

from pydantic import parse_obj_as, TypeAdapter

from orchd_sdk.models import SensorTemplate, Ref, Sensor

SENSOR_TEMPLATE_BASE_ROUTE = '/sensor_template/'
SENSORS_BASE_ROUTE = '/sensor/'


class SensorClient:

    def __init__(self, orchd_client):
        self.orchd_client = orchd_client

    async def get_sensor_templates(self):
        adapter = TypeAdapter(List[SensorTemplate])
        templates = await self.orchd_client.get(SENSOR_TEMPLATE_BASE_ROUTE)
        return adapter.validate_python(templates)

    async def get_sensor_template(self, template_id: str) -> SensorTemplate:
        template = await self.orchd_client.get(
            f'{SENSOR_TEMPLATE_BASE_ROUTE}{template_id}/')
        return SensorTemplate(**template)

    async def add_sensor_template(self,
                                  template: SensorTemplate) -> SensorTemplate:
        response = await self.orchd_client.post(SENSOR_TEMPLATE_BASE_ROUTE,
                                                template.model_dump())
        return SensorTemplate(**response)

    async def remove_sensor_template(self, template_id: str) -> str:
        response = await self.orchd_client.delete(
            f'{SENSOR_TEMPLATE_BASE_ROUTE}{template_id}/')
        return response

    async def get_sensors(self):
        adapter = TypeAdapter(List[Sensor])
        sensors = await self.orchd_client.get(SENSORS_BASE_ROUTE)
        return adapter.validate_python(sensors)

    async def get_sensor(self, sensor_id: str) -> Sensor:
        sensor = await self.orchd_client.get(f'{SENSORS_BASE_ROUTE}{sensor_id}/')
        return Sensor(**sensor)

    async def add_sensor(self, template_id: str) -> Sensor:
        response = await self.orchd_client.post(
            f'{SENSORS_BASE_ROUTE}', data=Ref(id=template_id).model_dump())
        return Sensor(**response)

    async def remove_sensor(self, sensor_id: str) -> str:
        response = await self.orchd_client.delete(f'{SENSORS_BASE_ROUTE}{sensor_id}/')
        return response

    async def stop_sensor(self, sensor_id: str) -> str:
        response = await self.orchd_client.post(f'{SENSORS_BASE_ROUTE}{sensor_id}/stop', data={})
        return response

    async def start_sensor(self, sensor_id: str) -> str:
        response = await self.orchd_client.post(f'{SENSORS_BASE_ROUTE}{sensor_id}/start', data={})
        return response