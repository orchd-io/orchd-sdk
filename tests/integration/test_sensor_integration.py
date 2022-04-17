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

import pytest

from orchd_sdk.models import Event
from orchd_sdk.sensor import LocalCommunicator
from orchd_sdk.reaction import global_reactions_event_bus


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
