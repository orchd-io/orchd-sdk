import importlib
import uuid
from abc import abstractmethod, ABC
from dataclasses import dataclass, field

from typing import Dict, Any, List, Union

from rx.core import Observer
from rx.subject import Subject


class Event:
    event_name: str
    data: Dict[str, str]

    def __init__(self, event_name: str, data: Any):
        self.id = str(uuid.uuid4())
        self.event_name = event_name
        self.data = data


@dataclass
class ReactionTemplate:
    """
    Representation of a possible :class:`ReactionTemplate` to be taken by a Node on a
    given event.

    Nodes can react on events detected in the network or internally in the node.
    Some example of possible events are:
    - Service Discovered
    - USB Device Attached
    - Service Down

    Attributes:
        name: the name of the :class:`ReactionTemplate`.
        handler: reaction event handler class - The class name.
        triggered_on: the event name that can trigger the action.
        handler_parameters: Handler specific parameters.
        active: Indiciation if the :class:`ReactionTemplate` is active or not.
    """
    name: str
    handler: str
    triggered_on: List[str]
    handler_parameters: Dict[str, Union[str, Dict]] = field(default_factory=dict)
    active: bool = True


class ReactionHandler(ABC):
    """
    A Reaction handler for a event.
    """

    @abstractmethod
    async def handle(self, event: str, reaction: ReactionTemplate) -> None:
        """
        Code to be executed as an reaction to an event.

        :param event: The event that triggered the action.
        :param reaction: The reaction object.
        """
        pass

    @abstractmethod
    def handle_error(self) -> None:
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

    def create_handler_object(self) -> ReactionHandler:
        """Instantiate a :class:`ReactionHandler` indicated
        in the reaction template."""
        class_parts = self.reaction_template.handler.split('.')
        class_name = class_parts.pop()
        module_name = '.'.join(class_parts)

        HandlerClass = getattr(importlib.import_module(module_name), class_name)
        self.handler = HandlerClass()

        return self.handler

    def on_next(self, value: Any) -> None:
        self.handler.handle(value, self.reaction_template)

    def on_error(self, error: Exception) -> None:
        self.handler.handle_error()


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
        name='io.orchd.reaction_template.DummyTemplate',
        triggered_on=["io.orchd.events.system.Test"],
        handler="orchd_sdk.event.DummyReactionHandler",
        handler_parameters=dict(),
        active=True
    )

    def __init__(self):
        super().__init__(DummyReaction.template)


class DummyReactionHandler(ReactionHandler):
    async def handle(self, event: str, reaction: ReactionTemplate) -> None:
        print("DummyReactionHandler.handle Called")

    def handle_error(self) -> None:
        print("DummyReactionHandler.handle_error Called")
        pass

