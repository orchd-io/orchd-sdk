from typing import Any
from abc import abstractmethod, ABC

from orchd_sdk.common import import_class
from orchd_sdk.errors import SinkError
from orchd_sdk.logging import logger
from orchd_sdk.models import SinkTemplate


class AbstractSink(ABC):
    """
    Implements the logic for a Sink.

    Sinks have only one objective, based o the given information via the template
    tries to "sink" data somewhere. This SOMEWHERE is defined by the Sink developer.
    Sinks are ideal for forwarding or storing data processed by `Reactions`.

    Inform the Reaction the Sinks that it must use and the Reaction will call the `sink`
    method os the Sink automatically after finishing its job.

    An example would be a Orchd Sensor subscribed to a MQTT subject capturing the data,
    a Reaction could capture the data and process it sinking the data in a CoAPSink that
    forwards the data to a CoAP based system.
    """

    def __init__(self, template: SinkTemplate):
        self._template = template

    @abstractmethod
    async def sink(self, data: Any):
        pass

    @abstractmethod
    async def close(self):
        pass


class DummySink(AbstractSink):
    """Dummy Sink for testing purposes"""

    template = SinkTemplate(sink_class='orchd_sdk.sink.DummySink',
                            name='io.orchd.sinks.DummySink',
                            version='0.1',
                            properties={'endpoint': 'https://example.com/test'})

    def __init__(self, template: SinkTemplate):
        super().__init__(template)

    async def sink(self, data):
        logger.debug(f'Data SUNK by Dummy! Actually, I did Nothing! :P {data}')

    async def close(self):
        pass


def sink_factory(template: SinkTemplate):
    try:
        Class = import_class(template.sink_class)
        if isinstance(Class, AbstractSink):
            raise SinkError('Sink class is not Valid!')
        return Class(template)
    except ModuleNotFoundError:
        raise SinkError('Sink class not found in PYTHONPATH.')

