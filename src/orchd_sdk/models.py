import uuid

from typing import Dict, List, Any

from pydantic import Field, BaseModel
from pydantic.types import UUID


class Event(BaseModel):
    event_name: str = Field(
        title='Event Name',
        description='A unique/namespaced name for the event.',
        regex=r'^\w[\w\._\-]+$',
        example='io.orchd.events.system.Test'
    )
    data: Dict[str, Any] = Field(
        default_factory=lambda: dict(),
        title='Event Data',
        description='Data attached to the event in the form of key/value pairs.'
    )
    id: UUID = Field(
        default_factory=uuid.uuid4,
        title='Event ID',
        description='Event Unique Identifier.'
    )

    class Config:
        additional_properties = False


class ReactionTemplate(BaseModel):
    """
    Representation of a Reaction Template to be used to create :class:`Reaction`s.

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
    name: str = Field(
        title='Reaction Template Name',
        description='A unique/namespaced name for the Reaction Template',
        regex=r'^\w[\w\._\-]+$',
        example='io.orchd.reaction_template.DummyTemplate'
    )
    version: str = Field(
        title='Template Version',
        description='Version of this reaction template.',
        example='1.0'
    )
    handler: str = Field(
        title='Handler Class',
        description='The full name/path of the handler Class',
        example='orchd_sdk.event.DummyReactionHandler'
    )
    triggered_on: List[str] = Field(
        title='Triggered On',
        description='List of event names that triggers the handler.',
        example=['io.orchd.events.system.Test']
    )
    handler_parameters: Dict[str, str] = Field(
        default_factory=dict,
        title='Handler Parameters',
        description='Parameters to be passed to the handler in the form key/value '
                    'pair.',
        example={'test_type': 'full'},
    )
    active: bool = Field(
        default=True,
        title='Active',
        description='Activate/Deactivate the availability of the template to create '
                    'new Reactions.',
        example=True
    )
    id: UUID = Field(
        default_factory=uuid.uuid4,
        title='Reaction Template ID',
        description='Unique Reaction Template identifier.',
        example='0a0866da-2a41-41a3-bcd9-9be9eedb2525'
    )
