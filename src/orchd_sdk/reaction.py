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

import asyncio
import importlib
import logging
import sys
import uuid

from abc import abstractmethod, ABC
from asyncio import AbstractEventLoop
from typing import Any, Dict, List, Union, Tuple

from reactivex.observer import Observer
from reactivex.subject import Subject

from orchd_sdk.common import import_class
from orchd_sdk.errors import SinkError, ReactionHandlerError, ReactionError
from orchd_sdk.models import Event, ReactionTemplate, SinkTemplate, ReactionInfo
from orchd_sdk.sink import AbstractSink, DummySink

logger = logging.getLogger(__name__)


class ReactionsEventBus:
    """
    The Reaction Event Bus.

    The Reaction Event Bus wraps a reactivex.subject.Subject and offers
    a method to register Reactions (they are reactivex.observer.Observer).

    Whenever ones wants to propagate an event on the system CAN do this
    through an global reaction event bus. However it is allowed to create
    more BUSES depending on the system architecture being implemented.
    """
    def __init__(self):
        self._subject = Subject()

    def register_reaction(self, reaction: "Reaction"):
        """Registers a Reaction (Observer) on the subject."""
        disposable = self._subject.subscribe(reaction)
        reaction.disposable = disposable

    def event(self, event_: Event):
        """Forwards the event to the subscribers"""
        self._subject.on_next(event_)

    def remove_all_reactions(self):
        """Unsubscribe all observers"""
        NotImplementedError()


class ReactionHandler(ABC):
    """
    A Reaction handler for a event.
    """

    @abstractmethod
    def handle(self, event: Event, reaction: ReactionTemplate) -> None:
        """
        Code to be executed as an reaction to an event.

        :param event: The event that triggered the action.
        :param reaction: The reaction object.
        """


class ReactionState:
    UNINITIALIZED = (1, 'PROVISIONING')
    READY = (2, 'READY')
    RUNNING = (3, 'RUNNING')
    STOPPED = (4, 'STOPPED')
    ERROR = (5, 'ERROR')
    FINALIZED = (6, 'FINALIZED')


class ReactionSinkManager:

    def __init__(self, reaction):
        self._sinks: Dict[str, AbstractSink] = dict()
        self.reaction: Reaction = reaction

    @property
    def sinks(self) -> List[AbstractSink]:
        return list(self._sinks.values())

    def add_sink(self, sink_template: SinkTemplate):
        try:
            SinkClass = import_class(sink_template.sink_class)
            sink: AbstractSink = SinkClass(sink_template)
            self._sinks[sink.id] = sink
            return sink
        except ModuleNotFoundError as e:
            raise SinkError(f'Not able to load Sink class {sink_template.sink_class}. '
                            f'Is it in PYTHONPATH?') from e

    async def create_sinks(self, sink_templates: List[SinkTemplate]) -> Dict[str, AbstractSink]:
        for template in sink_templates:
            try:
                self.add_sink(template)
            except SinkError as e:
                for sink in self.sinks:
                    await sink.close()
                    del self._sinks[sink.id]
                raise e

        return self._sinks

    async def remove_sink(self, sink_id):
        try:
            sink = self._sinks[sink_id]
            await sink.close()
            del self._sinks[sink_id]
        except KeyError as e:
            raise SinkError(f'Sink with given ID{sink_id} not Found!') from e

    def get_sink_by_id(self, sink_id):
        try:
            return self._sinks[sink_id]
        except KeyError as e:
            raise SinkError(f'Sink with given ID({sink_id}) Not Found!') from e

    async def close(self):
        for sink in self._sinks.values():
            await sink.close()
        self._sinks = dict()


class Reaction(Observer):
    """
    Reaction handling management class.

    This class instantiates the reaction handler and subscribes the Reaction
    to the events that triggers it.
    """

    def __init__(self, reaction_template: ReactionTemplate):
        super().__init__()
        self.state: Tuple = ReactionState.UNINITIALIZED
        self.handler: Union[ReactionHandler, None] = None
        self.disposable: Union[ReactionHandler, None] = None
        self.id = str(uuid.uuid4())
        self.reaction_template: ReactionTemplate = reaction_template
        self._loop: AbstractEventLoop = asyncio.get_event_loop()
        self.sink_manager = ReactionSinkManager(self)

    async def init(self):
        try:
            self.handler = self.create_handler_object()
            await self.sink_manager.create_sinks(self.reaction_template.sinks)
        except SinkError as e:
            self.state = ReactionState.ERROR
            raise ReactionError("While creating reaction, an error occurred preparing Sinks.") from e
        except ReactionHandlerError as e:
            self.state = ReactionState.ERROR
            raise ReactionError("While creating reaction, an error occurred preparing Reaction Handlers.") from e

        self.state = ReactionState.READY
        return self

    @property
    def sinks(self) -> List[AbstractSink]:
        return list(self.sink_manager.sinks)

    def status(self):
        return ReactionInfo(
            id=self.id,
            state=self.state[1],
            template=self.reaction_template,
            sinks_instances=[s.info for s in self.sink_manager.sinks]
        )

    def create_handler_object(self) -> ReactionHandler:
        """Instantiate a :class:`ReactionHandler` indicated
        in the reaction template."""
        class_parts = self.reaction_template.handler.split('.')
        class_name = class_parts.pop()
        module_name = '.'.join(class_parts)

        try:
            if module_name not in sys.modules:
                importlib.import_module(module_name)
            HandlerClass = getattr(sys.modules.get(module_name), class_name)
            self.handler = HandlerClass()
            return self.handler
        except (ModuleNotFoundError, AttributeError) as e:
            raise ReactionHandlerError(f'Reaction Handler module/class '
                                       f'{self.reaction_template.handler} not found!') from e

    def on_next(self, event: Event) -> None:
        if event.event_name in self.reaction_template.triggered_on or \
                '' in self.reaction_template.triggered_on:
            self.sink(self.handler.handle(event, self.reaction_template))

    def sink(self, data):
        for sink in self.sink_manager.sinks:
            logger.info(f"Sink {sink.id} scheduled to be executed.")
            self._loop.create_task(sink.sink(data))

    def activate(self, event_bus: ReactionsEventBus):
        event_bus.register_reaction(self)
        logger.debug(f'Reaction for template {self.reaction_template.id} '
                     f'Activated. ID({self.id}).')
        self.state = ReactionState.RUNNING

    def dispose(self) -> None:
        self.disposable.dispose()
        super().dispose()
        self.disposable = None
        self.state = ReactionState.STOPPED

    async def stop(self):
        self.dispose()

    async def close(self):
        if self.state == ReactionState.RUNNING:
            self.dispose()
        await self.sink_manager.close()
        self.state = ReactionState.FINALIZED


class DummyReaction(Reaction):
    """Dummy Reaction used system tests during runtime."""

    template = ReactionTemplate(
        id='cfe5b2cd-fb15-4ca6-888f-6a770d1a4e6a',
        name='io.orchd.reaction_template.DummyTemplate',
        version='1.0',
        triggered_on=['io.orchd.events.system.Test'],
        handler="orchd_sdk.reaction.DummyReactionHandler",
        sinks=[DummySink.template],
        handler_parameters=dict(),
        active=True
    )

    def __init__(self, custom_template: ReactionTemplate = None):
        super().__init__(custom_template or DummyReaction.template)


class DummyReactionHandler(ReactionHandler):
    """
    A Dummy ReactionHandler that is used in system tests.
    """
    def handle(self, event: Event, reaction: ReactionTemplate) -> Any:
        logger.info(f'DummyReactionHandler.handle Called')


global_reactions_event_bus = ReactionsEventBus()
"""System wide ReactionEventBus"""
