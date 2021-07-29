import pytest

from orchd_sdk.errors import SinkError
from orchd_sdk.models import SinkTemplate
from orchd_sdk.sink import sink_factory, DummySink, AbstractSink


def test_sink_factory():
    sink = sink_factory(DummySink.template)
    assert sink is not None
    assert isinstance(sink, AbstractSink) is True

    with pytest.raises(SinkError):
        template: SinkTemplate = DummySink.template.copy()
        template.sink_class = 'not.existent.Class'
        sink_factory(template)
