from typing import Any
from abc import abstractmethod, ABC

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
    def sink(self, data: Any):
        pass


class DummySink(AbstractSink):
    """Dummy Sink for testing purposes"""

    def __init__(self, template: SinkTemplate):
        super().__init__(template)

    def sink(self, data):
        logger.debug(f'Data SUNK by Dummy! {data}')
