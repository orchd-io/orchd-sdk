import pytest

from orchd_sdk.models import Event
from orchd_sdk.sensor import LocalCommunicator
from orchd_sdk.event import global_reactions_event_bus


class TestLocalCommunicatorIntegration:
    """
    Tests the LocalCommunicator class
    """

    @pytest.mark.asyncio
    async def test_emit_event(self):
        """
        Tests if the emitted event is captured by subscribers.

        The test uses a LocalCommunicator to emit an event.
        """
        comm = LocalCommunicator()
        result = None

        def on_next(value):
            nonlocal result
            result = value

        disposable = global_reactions_event_bus._subject.subscribe(on_next=on_next)
        event = Event(event_name='io.orchd.event.system.Test',
                      data=dict())

        await comm.emit_event(event)
        assert type(result) == Event
        assert result is event

        disposable.dispose()
