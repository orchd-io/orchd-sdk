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

from typing import List
from unittest.mock import patch, Mock
from uuid import uuid4

import pytest
import pytest_asyncio

from orchd_sdk.errors import ReactionError, SinkError
from orchd_sdk.models import Event, SinkTemplate
from orchd_sdk.reaction import DummyReaction, ReactionsEventBus, ReactionHandler, ReactionState, ReactionSinkManager
from orchd_sdk.sink import DummySink


@pytest.fixture
def test_event():
    return Event(event_name='io.orchd.events.system.Test',
                 data=dict())


@pytest.fixture(scope='function')
def dummy_reaction_template():
    yield DummyReaction.template.model_copy()


@pytest.fixture(scope='function')
def dummy_sink_template():
    yield DummySink.template.model_copy()


@pytest.fixture(scope='function')
def dummy_sink_template_list() -> List[SinkTemplate]:
    yield [
        DummySink.template.model_copy(update={'id': str(uuid4())}),
        DummySink.template.model_copy(update={'id': str(uuid4())}),
        DummySink.template.model_copy(update={'id': str(uuid4())})
    ]


@pytest_asyncio.fixture(scope='function')
async def reaction_sink_manager():
    reaction = DummyReaction()
    await reaction.init()
    yield ReactionSinkManager(reaction)
    await reaction.close()


class TestReaction:
    """
    Test is the ReactionHandler is invoked when expected.
    """

    @pytest.mark.asyncio
    async def test_must_initialize_handlers_on_creation(self, dummy_reaction_template):
        reaction = DummyReaction(dummy_reaction_template)
        await reaction.init()

        assert reaction.handler is not None
        assert issubclass(reaction.handler.__class__, ReactionHandler) is True

    @pytest.mark.asyncio
    async def test_must_initialize_sinks_on_creation(self, dummy_reaction_template):
        reaction = DummyReaction(dummy_reaction_template)
        await reaction.init()

        num_of_sinks_in_template = len(reaction.reaction_template.sinks)
        assert len(reaction.sink_manager.sinks) == num_of_sinks_in_template

    @pytest.mark.asyncio
    async def test_initialization_must_fail_if_reaction_class_is_not_loaded(self, dummy_reaction_template):
        dummy_reaction_template.handler = 'nonexistent.Class'

        with pytest.raises(ReactionError):
            await DummyReaction(dummy_reaction_template).init()

    @pytest.mark.asyncio
    async def test_initialization_must_fail_if_sink_class_is_not_in_pythonpath(self, dummy_reaction_template):
        sink_template_with_nonexistent_class: SinkTemplate = DummySink.template.model_copy()
        sink_template_with_nonexistent_class.sink_class = 'nonexistent.Class'
        dummy_reaction_template.sinks = [sink_template_with_nonexistent_class]

        with pytest.raises(ReactionError):
            await DummyReaction(dummy_reaction_template).init()

    def test_status_must_be_UNINITIALIZED_at_creation(self):
        reaction = DummyReaction()
        assert reaction.state == ReactionState.UNINITIALIZED

    @pytest.mark.asyncio
    async def test_status_must_be_READY_if_initialized_successfuly_but_and_not_started(self, dummy_reaction_template):
        dummy_reaction_template.active = False
        reaction = DummyReaction(dummy_reaction_template)
        await reaction.init()

        assert reaction.state == ReactionState.READY

    @pytest.mark.asyncio
    async def test_status_must_be_RUNNING_if_initialized_and_activated(self, dummy_reaction_template,
                                                                 reaction_event_bus):
        dummy_reaction_template.active = True
        reaction = DummyReaction(dummy_reaction_template)
        await reaction.init()
        reaction.activate(reaction_event_bus)

        assert reaction.state == ReactionState.RUNNING

    @pytest.mark.asyncio
    async def test_status_must_be_ERROR_if_initialization_failed(self, dummy_reaction_template):
        dummy_reaction_template.handler = 'nonexistent.class'

        with pytest.raises(ReactionError):
            reaction = DummyReaction(dummy_reaction_template)
            await reaction.init()
            assert reaction.state == ReactionState.ERROR

    @pytest.mark.asyncio
    async def test_status_must_be_STOPPED_if_manually_stopped(self, reaction_event_bus):
        reaction = DummyReaction()
        reaction.activate(reaction_event_bus)
        await reaction.stop()

        assert reaction.state == ReactionState.STOPPED

    @pytest.mark.asyncio
    async def test_must_unsubscribe_from_bus_if_stopped_if_transitioning_from_RUNNING(self, reaction_event_bus):
        reaction = DummyReaction()
        reaction.activate(reaction_event_bus)

        await reaction.stop()
        assert reaction.state == ReactionState.STOPPED
        assert reaction.disposable is None
        assert len(reaction_event_bus._subject.observers) == 0

    @pytest.mark.asyncio
    async def test_status_must_be_RUNNING_if_activated_after_stopping(self, reaction_event_bus):
        reaction = DummyReaction()
        await reaction.init()
        reaction.activate(reaction_event_bus)
        await reaction.stop()

        assert reaction.state == ReactionState.STOPPED

        reaction.activate(reaction_event_bus)
        assert reaction.state == ReactionState.RUNNING

    @pytest.mark.asyncio
    async def test_reaction_must_calls_handler_on_event(self, test_event):
        """
        Tests if a reaction will handle the event when received.
        """
        reaction = DummyReaction()
        await reaction.init()
        with patch.object(reaction.handler, 'handle') as mock:
            reaction.on_next(test_event)

            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_reaction_must_call_handler_when_event_injected_on_event_bus(self, test_event):
        """
        test the handling of an event when it comes from the ReactionEventBus.
        """
        event_bus = ReactionsEventBus()
        reaction = DummyReaction()
        await reaction.init()

        handle_mock = Mock()
        reaction.handler.handle = handle_mock

        event_bus.register_reaction(reaction)

        event_bus.event(test_event)
        handle_mock.assert_called()
        handle_mock.reset_mock()

    @pytest.mark.asyncio
    async def test_must_unregister_from_bus_on_close(self, reaction_event_bus):
        reaction = DummyReaction()
        await reaction.init()
        reaction.activate(reaction_event_bus)

        assert len(reaction_event_bus._subject.observers) == 1
        await reaction.close()
        assert len(reaction_event_bus._subject.observers) == 0

    @pytest.mark.asyncio
    async def test_must_trasition_to_FINALIZED_state_when_closed(self, reaction_event_bus):
        reaction = DummyReaction()
        await reaction.init()

        await reaction.close()
        assert reaction.state == ReactionState.FINALIZED

    @pytest.mark.asyncio
    async def test_must_release_sink_manager_when_closed(self):
        reaction = DummyReaction()
        await reaction.init()

        assert len(reaction.sinks) == 1
        await reaction.close()
        assert len(reaction.sinks) == 0


class TestReactionSinkManager:

    def test_add_sink_must_fail_if_sink_class_do_not_exists(self, reaction_sink_manager, dummy_sink_template):
        with pytest.raises(SinkError):
            dummy_sink_template.sink_class = 'nonexistent.SinkClass'
            reaction_sink_manager.add_sink(dummy_sink_template)

    def test_add_sink_must_succeed_if_class_exists(self, reaction_sink_manager, dummy_sink_template):
        reaction_sink_manager.add_sink(dummy_sink_template)
        assert len(reaction_sink_manager.sinks) == 1

    @pytest.mark.asyncio
    async def test_create_multiple_valid_sinks(self, reaction_sink_manager, dummy_sink_template_list):
        sinks = await reaction_sink_manager.create_sinks(dummy_sink_template_list)
        assert len(sinks) == len(dummy_sink_template_list)

    @pytest.mark.asyncio
    async def test_when_failing_to_create_a_bulk_of_sinks_close_the_already_created(
            self, reaction_sink_manager, dummy_sink_template_list):

        dummy_sink_template_list[2].sink_class = 'nonexistent.SinkClass'
        with patch.object(DummySink, 'close') as close:
            with pytest.raises(SinkError):
                await reaction_sink_manager.create_sinks(dummy_sink_template_list)
            assert close.await_count == 2

    @pytest.mark.asyncio
    async def test_when_failing_to_create_a_bulk_of_sinks_remove_the_already_created(
            self, reaction_sink_manager, dummy_sink_template_list):

        dummy_sink_template_list[2].sink_class = 'nonexistent.SinkClass'
        with pytest.raises(SinkError):
            await reaction_sink_manager.create_sinks(dummy_sink_template_list)
        assert len(reaction_sink_manager.sinks) == 0

    @pytest.mark.asyncio
    async def test_get_sink_by_an_existent_id(self, dummy_sink_template_list, reaction_sink_manager):
        await reaction_sink_manager.create_sinks(dummy_sink_template_list)
        sink = reaction_sink_manager.sinks[0]
        retrieved_sink = reaction_sink_manager.get_sink_by_id(sink.id)

        assert retrieved_sink.id == sink.id

    @pytest.mark.asyncio
    async def test_get_sink_must_through_error_when_id_do_not_exists(self, reaction_sink_manager):
        with pytest.raises(SinkError):
            reaction_sink_manager.get_sink_by_id('some_nonexistent_id')

    @pytest.mark.asyncio
    async def test_when_removing_sink_existent_sink_close_it(self, reaction_sink_manager, dummy_sink_template_list):
        await reaction_sink_manager.create_sinks(dummy_sink_template_list)
        sink_to_remove = reaction_sink_manager.sinks[0]

        with patch.object(DummySink, 'close') as close:
            await reaction_sink_manager.remove_sink(sink_to_remove.id)
            close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_when_removing_a_sink_remove_from_sink_list(self, reaction_sink_manager, dummy_sink_template_list):
        await reaction_sink_manager.create_sinks(dummy_sink_template_list)
        sink = reaction_sink_manager.sinks[0]
        sink_count_expected = len(reaction_sink_manager.sinks) - 1

        await reaction_sink_manager.remove_sink(sink.id)
        assert sink_count_expected == len(reaction_sink_manager.sinks)

    @pytest.mark.asyncio
    async def test_when_removing_nonexistent_sink_throw_error(self, reaction_sink_manager):
        with pytest.raises(SinkError):
            await reaction_sink_manager.remove_sink('some_nonexistent_id')
