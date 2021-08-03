import asyncio
import importlib
import json
from asyncio import AbstractEventLoop

import sys

from os import path
from abc import abstractmethod, ABC

from typing import Any, List, Dict

from rx.core.observer import Observer
from rx.core.typing import Disposable
from rx.subject import Subject

from orchd_sdk.errors import SinkError
from orchd_sdk.logging import logger
from orchd_sdk.common import import_class
from orchd_sdk.models import Event, ReactionTemplate, SinkTemplate
from orchd_sdk.sink import AbstractSink, DummySink

REACTION_SCHEMA_FILE = path.join(path.dirname(path.realpath(__file__)),
                                 'reaction.schema.json')


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


class Reaction(Observer):
    """
    Reaction handling management class.

    This class instantiates the reaction handler and subscribes the Reaction
    to the events that triggers it.
    """

    def __init__(self, reaction_template: ReactionTemplate):
        super().__init__()
        self.disposable: Disposable = ...
        self._sinks: Dict[str, AbstractSink] = dict()
        self.reaction_template: ReactionTemplate = reaction_template
        self.handler: ReactionHandler = self.create_handler_object()
        self._loop: AbstractEventLoop = asyncio.get_event_loop()
        self.create_sinks()

    @property
    def sinks(self):
        return self._sinks

    def create_handler_object(self) -> ReactionHandler:
        """Instantiate a :class:`ReactionHandler` indicated
        in the reaction template."""
        class_parts = self.reaction_template.handler.split('.')
        class_name = class_parts.pop()
        module_name = '.'.join(class_parts)

        if module_name not in sys.modules:
            importlib.import_module(module_name)
        HandlerClass = getattr(sys.modules.get(module_name), class_name)
        self.handler = HandlerClass()

        return self.handler

    def create_sinks(self) -> Dict[str, AbstractSink]:
        for sink in self.reaction_template.sinks:
            try:
                self.add_sink(sink)
            except SinkError as e:
                raise SinkError('Sink creation failed!') from e

        return self._sinks

    def add_sink(self, sink_template: SinkTemplate):
        try:
            SinkClass = import_class(sink_template.sink_class)
            sink: AbstractSink = SinkClass(sink_template)
            self._sinks[sink.id] = sink
        except ModuleNotFoundError as e:
            raise SinkError('Not able to load Sink class. Is it in PYTHONPATH?')

    def on_next(self, event: Event) -> None:
        if event.event_name in self.reaction_template.triggered_on or \
                '' in self.reaction_template.triggered_on:
            self.sink(self.handler.handle(event, self.reaction_template))

    def sink(self, data):
        for sink in self._sinks.values():
            self._loop.create_task(sink.sink(data))

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

    def close(self):
        self.dispose()
        for sink in self._sinks.values():
            sink.close()


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

    def register_reaction(self, reaction: Reaction):
        """Registers a Reaction (Observer) on the subject."""
        disposable = self._subject.subscribe(reaction)
        reaction.disposable = disposable

    def event(self, event_: Event):
        """Forwards the event to the subscribers"""
        self._subject.on_next(event_)

    def remove_all_reactions(self):
        """Unsubscribe all observers"""
        NotImplementedError()


class DummyReaction(Reaction):
    """Dummy Reaction used system tests during runtime."""

    template = ReactionTemplate(
        id='cfe5b2cd-fb15-4ca6-888f-6a770d1a4e6a',
        name='io.orchd.reaction_template.DummyTemplate',
        version='1.0',
        triggered_on=['io.orchd.events.system.Test'],
        handler="orchd_sdk.event.DummyReactionHandler",
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
