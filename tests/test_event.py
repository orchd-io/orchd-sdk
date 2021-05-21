from unittest.mock import patch

import pytest
import asyncio
import datetime
from orchd_sdk.event import DummyReactionHandler, Event, DummyReaction, \
    ReactionsEventBus
from orchd_sdk.logging import logger


class TestReactionHandler:

    @pytest.mark.asyncio
    async def test_reaction_handling_async(self):
        handler = DummyReactionHandler()

        loop = asyncio.get_event_loop()
        f = loop.create_task(handler.handle(Event("SomeEvent", dict()),
                                            DummyReaction.template))
        logger.info(f"{datetime.datetime.now()} Async checked!")
        await f
        logger.info(f"{datetime.datetime.now()} finished!")

    @pytest.mark.asyncio
    async def test_reaction_on_next(self):
        with patch("orchd_sdk.event.DummyReactionHandler.handle") as mock:
            reaction = DummyReaction()
            reaction.on_next("some_value")

            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_with_reaction_event_bus(self):
        event_bus = ReactionsEventBus()
        event_bus.register_reaction(DummyReaction())
        with patch("orchd_sdk.event.DummyReactionHandler.handle") as mock:
            event_bus.event(Event('io.orchd.events.system.Test', ""))
            mock.assert_called_once()
