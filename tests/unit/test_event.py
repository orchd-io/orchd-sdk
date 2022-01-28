from unittest.mock import patch,  Mock

import pytest
from orchd_sdk.reaction import DummyReaction, ReactionsEventBus
from orchd_sdk.models import Event


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
        reaction = await DummyReaction().init()
        with patch.object(reaction.handler, 'handle') as mock:
            reaction.on_next(test_event)

            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_with_reaction_event_bus(self, test_event):
        """
        test the handling of an event when it comes from the ReactionEventBus.
        """
        event_bus = ReactionsEventBus()
        reaction = await DummyReaction().init()
        handle_mock = Mock()
        reaction.handler.handle = handle_mock

        event_bus.register_reaction(reaction)

        event_bus.event(test_event)
        handle_mock.assert_called()
        handle_mock.reset_mock()
