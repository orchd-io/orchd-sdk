import asyncio
import importlib
import json
import logging
import uuid
from asyncio import AbstractEventLoop

import sys

from os import path
from abc import abstractmethod, ABC

from typing import Any, Dict, List

from rx.core.observer import Observer
from rx.core.typing import Disposable
from rx.subject import Subject

from orchd_sdk.errors import SinkError, ReactionHandlerError, ReactionError
from orchd_sdk.common import import_class
from orchd_sdk.models import Event, ReactionTemplate, SinkTemplate, ReactionInfo
from orchd_sdk.sink import AbstractSink, DummySink

REACTION_SCHEMA_FILE = path.join(path.dirname(path.realpath(__file__)),
                                 'reaction.schema.json')


logger = logging.getLogger(__name__)


class ReactionsEventBus:
    """
    The Reaction Event Bus.

    The Reaction Event Bus wraps a rx.subject.Subject and offers
    a method to register Reactions (they are rx.core.observer.Observers).

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
        pass


class ReactionState:
    PROVISIONING = (1, 'PROVISIONING')
    READY = (2, 'READY')
    RUNNING = (3, 'RUNNING')
    STOPPED = (4, 'STOPPED')
    ERROR = (5, 'ERROR')


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
            raise SinkError('Not able to load Sink class. Is it in PYTHONPATH?') from e

    async def create_sinks(self) -> Dict[str, AbstractSink]:
        for sink in self.reaction.reaction_template.sinks:
            try:
                self.add_sink(sink)
            except SinkError as e:
                for sink in self.sinks:
                    await sink.close()
                raise SinkError('Error instantiating Reaction Sinks.') from e

        return self._sinks

    async def remove_sink(self, sink_id):
        sink = self._sinks[sink_id]
        await sink.close()
        del self._sinks[sink_id]

    def get_sink_by_id(self, sink_id):
        try:
            return self._sinks[sink_id]
        except KeyError as e:
            raise SinkError(f'Sink with given ID({sink_id}) Not Found!') from e

    async def close(self):
        for sink in self._sinks.values():
            await sink.close()


class Reaction(Observer):
    """
    Reaction handling management class.

    This class instantiates the reaction handler and subscribes the Reaction
    to the events that triggers it.
    """

    def __init__(self, reaction_template: ReactionTemplate):
        super().__init__()
        self.state = ReactionState.PROVISIONING
        self.handler: ReactionHandler = ...
        self.disposable: Disposable = ...
        self.id = str(uuid.uuid4())
        self.reaction_template: ReactionTemplate = reaction_template
        self._loop: AbstractEventLoop = asyncio.get_event_loop()
        self.sink_manager = ReactionSinkManager(self)

    async def init(self):
        try:
            self.handler = self.create_handler_object()
            await self.sink_manager.create_sinks()
        except SinkError as e:
            self.state = ReactionState.ERROR
            raise ReactionError("While creating reaction, an error occurred preparing Sinks.") from e
        except ReactionHandlerError as e:
            self.state = ReactionState.ERROR
            raise ReactionError("While creating reaction, an error occurred preparing Reaction Handlers.") from e

        self.state = ReactionState.READY

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
            self._loop.create_task(sink.sink(data))

    def activate(self, event_bus: ReactionsEventBus):
        event_bus.register_reaction(self)
        logger.debug(f'Reaction for template {self.reaction_template.id} '
                     f'Activated. ID({self.id}).')
        self.state = ReactionState.RUNNING

    @staticmethod
    def schema() -> str:
        """
        Load the :class:`ReactionTemplate` schema definition.

        :return: Return the schema as string.
        """
        with open(REACTION_SCHEMA_FILE) as fd:
            schema = json.loads(fd.read())
        return schema

    def dispose(self) -> None:
        self.disposable.dispose()
        super().dispose()
        self.disposable = None
        self.state = ReactionState.STOPPED

    async def close(self):
        if self.state == ReactionState.RUNNING:
            self.dispose()
        await self.sink_manager.close()


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

    def __init__(self):
        super().__init__(DummyReaction.template)


class DummyReactionHandler(ReactionHandler):
    """
    A Dummy ReactionHandler that is used in system tests.
    """
    def handle(self, event: Event, reaction: ReactionTemplate) -> Any:
        logger.info(f'DummyReactionHandler.handle Called')


global_reactions_event_bus = ReactionsEventBus()
"""System wide ReactionEventBus"""
