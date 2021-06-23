import asyncio
import importlib
import json
import sys

from os import path
from abc import abstractmethod, ABC

from typing import Any

from rx.core import Observer
from rx.subject import Subject

from orchd_sdk.logging import logger
from orchd_sdk.models import Event, ReactionTemplate

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
        self.reaction_template = reaction_template
        self.handler = self.create_handler_object()
        self._loop = asyncio.get_event_loop()

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

    def on_next(self, event: Event) -> None:
        if event.event_name in self.reaction_template.triggered_on or \
                '' in self.reaction_template.triggered_on:
            self.handler.handle(event, self.reaction_template)

    @staticmethod
    def schema() -> str:
        """
        Load the :class:`ReactionTemplate` schema definition.

        :return: Return the schema as string.
        """
        with open(REACTION_SCHEMA_FILE) as fd:
            schema = json.loads(fd.read())
        return schema


class ReactionsEventBus:
    def __init__(self):
        self._subject = Subject()

    def register_reaction(self, reaction: Reaction):
        self._subject.subscribe(reaction)

    def event(self, event_: Event):
        self._subject.on_next(event_)

    def remove_all_reactions(self):
        self._subject.dispose()


class DummyReaction(Reaction):
    """Dummy Reaction used system tests during runtime."""

    template = ReactionTemplate(
        id='cfe5b2cd-fb15-4ca6-888f-6a770d1a4e6a',
        name='io.orchd.reaction_template.DummyTemplate',
        version='1.0',
        triggered_on=["io.orchd.events.system.Test"],
        handler="orchd_sdk.event.DummyReactionHandler",
        handler_parameters=dict(),
        active=True
    )

    def __init__(self):
        super().__init__(DummyReaction.template)


class DummyReactionHandler(ReactionHandler):
    def handle(self, event: Event, reaction: ReactionTemplate) -> Any:
        logger.info(f'DummyReactionHandler.handle Called')
