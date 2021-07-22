import uuid

from typing import Dict, List, Any, Union, Optional

from pydantic import Field, BaseModel


def uuid_str_factory():
    return str(uuid.uuid4())


class Event(BaseModel):
    """
    Representation of an event of the Orchd system.

    An event have a name and data associated. Each event have
    an unique ID. They are propagated into the Orchd System usually
    by Sensors and captured by Reactions that can react to it.
    """
    event_name: str = Field(
        title='Event Name',
        description='A unique/namespaced name for the event.',
        regex=r'^\w[\w\._\-]+$',
        example='io.orchd.events.system.Test'
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        title='Event Data',
        description='Data attached to the event in the form of key/value pairs.'
    )
    id: str = Field(
        default_factory=uuid_str_factory,
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
    id: str = Field(
        default_factory=uuid_str_factory,
        title='Reaction Template ID',
        description='Unique Reaction Template identifier.',
        example='0a0866da-2a41-41a3-bcd9-9be9eedb2525'
    )


class SensorTemplate(BaseModel):
    """
    Representation of a Sensor Template describing the Sensor characteristics.

    A Sensor is intended to detect events outside the system and inject tem into
    it. The SensorTemplate is responsible to hold metadata about a Sensor to be
    instantiated. By having a SensorTemplate it is possible to instantiate a Sensor.
    Important information comes with the template, as an example a set of properties
    that can be used by the sensor to configure its behavior.
    """
    id: str = Field(
        title='Id',
        description='Unique identification of the Sensor',
        example='0ba3376f-64b8-4ecf-a579-66c353100e1c',
        default_factory=uuid_str_factory
    )

    name: str = Field(
        title='Sensor\'s Name',
        description='The namespaced name of the Sensor',
        regex=r'^\w[\w\._\-]+$',
        example='io.orchd.sensor.template.DummySensorTemplate'
    )

    version: str = Field(
        title='Version',
        description='Sensor\'s version',
        example='1.0'
    )

    sensor: str = Field(
        title='Sensor Class',
        description='Class that implements the Sensor',
        example='orchd_sdk.sensor.DummySensor'
    )

    sensing_interval: float = Field(
        title='Sensing Interval',
        description='Interval between two consecutive sense calls in seconds.',
        example=0.1
    )

    communicator: str = Field(
        title='Communicator Class',
        description='Class of the Communicator to used.',
        example='orchd_sdk.sensor.LocalCommunicator'
    )

    parameters: Dict[str, Union[str, int, float]] = Field(
        title='Sensor Parameters',
        description='Parameters to be used by the Sensor during Runtime',
        example={'poll_interval': 3}
    )

    description: str = Field(
        title='Description',
        description='Description of the Sensor',
        example='Sense for changes in a Dummy value in the System'
    )


class Sensor(BaseModel):
    """
    Represents the state and data of a Sensor
    """
    id: str = Field(
        title='Sensor Id',
        description='Id of the sensor.',
        example='7447f5f8-63f6-48d0-8537-5fae0b30015d'
    )

    template: SensorTemplate = Field(
        title='Sensor Template',
        description='Template related to the Sensor.',
        example='orchd_sdk.sensor.DummySensor'
    )

    status: tuple = Field(
        title='Sensor Status',
        description='Current status of the Sensor.',
        example=(2, 'READY')
    )

    events_count: Optional[int] = Field(
        title='Events Counter',
        description='Number of events sensed by the sensor.',
        example=1002
    )

    events_forwarded: Optional[int] = Field(
        title='Forwarded Events',
        description='Number of events sensed and forwarded to Orchd.',
        example=540
    )

    events_discarded: Optional[int] = Field(
        title='Events discarded',
        description='Number of events sensed, captured but discarded.'
    )


class Id(BaseModel):
    """
    Represents an Id and associated possible additional info.

    This model is intended to be used when sending Id over the network.
    Many operations, e.g. HTTP services requires IDs to be sent as payload,
    this model makes it easy to serialized/deserialize the Id in the source
    and destination.
    """

    id: str = Field(
        title='ID',
        description='An ID.',
        example='0ccb8b84-c52d-4a6a-af6b-a2c273745825'
    )

    metadata: Optional[Dict[str, str]] = Field(
        title='ID Metadata',
        description='Optional field with Key/Value pairs with additional info about '
                    'the id.',
        example={'related_model': 'SomeModelClass'}
    )

