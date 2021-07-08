from unittest.mock import patch, AsyncMock, Mock

import pytest
import asyncio
import datetime
from orchd_sdk.event import DummyReactionHandler, DummyReaction, \
    ReactionsEventBus
from orchd_sdk.models import Event
from orchd_sdk.logging import logger


@pytest.fixture
def test_event():
    return Event(event_name='io.orchd.events.system.Test',
                 data=dict())


class TestReactionHandler:
    """
    Test is the ReactionHandler is invoked when expected.
    """

    @pytest.mark.asyncio
    async def test_reaction_on_next(self, test_event):
        """
        Tests if a reaction will handle the event when received.
        """
        reaction = DummyReaction()
        with patch.object(reaction.handler, 'handle') as mock:
            reaction.on_next(test_event)

            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_with_reaction_event_bus(self, test_event):
        """
        test the handling of an event when it comes from the ReactionEventBus.
        """
        event_bus = ReactionsEventBus()
        reaction = DummyReaction()
        handle_mock = Mock()
        reaction.handler.handle = handle_mock

        event_bus.register_reaction(reaction)

        event_bus.event(test_event)
        handle_mock.assert_called()
        handle_mock.reset_mock()

