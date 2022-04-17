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

import uuid

from typing import Dict, List, Any, Union, Optional

from pydantic import Field, BaseModel

import orchd_sdk
from orchd_sdk import util


def uuid_str_factory():
    return str(uuid.uuid4())


class Ref(BaseModel):
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

    metadata: Any = Field(
        title='ID Metadata',
        description='Optional field with Key/Value pairs with additional info about '
                    'the id.',
        example={'related_model': 'SomeModelClass'}
    )


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


class SinkTemplate(BaseModel):
    """
    Representation of an Orchd Sink

    The properties are Sink implementation specific and the allowed options must be
    defined in the Sink implementation docs.
    """
    id: str = Field(
        default_factory=uuid_str_factory,
        title='Sink Template Id',
        description='Id of the Sink Template',
        example='3d2077c7-dbad-4975-b769-a8da870cf5f6'
    )

    name: str = Field(
        title='Sink\'s Template name',
        description='A descriptive name for the Sink.',
        example='io.orchd.sinks.MyMainSink'
    )

    version: str = Field(
        title='Sink\'s Template Version',
        description='Version of this Sink.',
        example='0,1'
    )

    sink_class: str = Field(
        title='Sink Template Class',
        description='Sink Class to be used to instantiate sinks.',
        example='orchd_sdk.sink.DummySink'
    )

    properties: Dict[str, str] = Field(
        title='Sink Properties',
        description='key/value pairs with Sink specific properties',
        example={'endpoint': 'http//www.example.com/test'}
    )


class Sink(BaseModel):
    """
    Sink instance information.

    Sink instances are attached to Reactions, this model represents the status of
    sink instances.
    """
    id: str = Field(
        default_factory=uuid_str_factory,
        title='Sink Id',
        description='Id of the Sink',
        example='3d2077c7-dbad-4975-b769-a8da870cf5f6'
    )

    template: SinkTemplate = Field(
        title='Sink Template',
        description='Sink Template used to instantiate the Sink',
        example=SinkTemplate(sink_class='orchd_sdk.sink.DummySink',
                             name='io.orchd.sinks.DummySink',
                             version='0.1',
                             properties={'endpoint': 'https://example.com/test'})
    )


class ReactionTemplate(BaseModel):
    """
    Representation of a Reaction Template to be used to create `Reaction`.

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
        example='orchd_sdk.reaction.DummyReactionHandler'
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

    sinks: Optional[List[SinkTemplate]] = Field(
        title='Sinks',
        default_factory=list,
        description='Sinks used by reactions created from this template.',
        example=[SinkTemplate(sink_class='orchd_sdk.sink.DummySink',
                              name='io.orchd.sinks.DummySink',
                              version='0.1',
                              properties={'endpoint': 'https://example.com/test'})]
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

    parameters: Dict[str, Union[str, int, float, List[Union[str, int, float]]]] = \
        Field(title='Sensor Parameters',
              description='Parameters to be used by the Sensor during Runtime',
              example={'poll_interval': 3}
    )

    description: str = Field(
        title='Description',
        description='Description of the Sensor',
        example='Sense for changes in a Dummy value in the System'
    )


class ReactionInfo(BaseModel):
    """
    Represents the state and info of an Reaction instance.
    """
    id: str = Field(
        title='Reaction Id',
        description='Id of the Reaction.',
        example='cdc51818-6ebe-4931-bed2-2a297c70681e'
    )

    state: str = Field(
        title='State',
        description='Current Reaction state.',
        example='READY'
    )

    template: ReactionTemplate = Field(
        title='Reaction Template',
        description='Reaction Template used to instantiate this Reaction.',
        example='d818d8ff-f859-4239-8602-103563b8a2ff'
    )

    sinks_instances: List[Sink] = Field(
        title='Sinks\' IDs',
        description='Id of Sinks associated to this reaction',
        example=['1d1c79de-7170-4dc6-aae1-9504ea7c793e',
                 'eaaf2065-484e-4c31-88fa-c3b422aa8927']
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


class Project(BaseModel):
    class Config:
        validate_assignment = True

    def __init__(self, **kwargs):
        main_package_name = util.kebab_case_to_snake_case(kwargs.get('name'))
        kwargs['main_package'] = main_package_name
        super().__init__(**kwargs)

    orchd_sdk_version = orchd_sdk.version()
    version: str = '0.0'
    author: str = 'unknown'
    description: str = 'no description'
    license: str = 'unknown'
    name: str = Field(
        title='Name of the Project',
        pattern='^((_?[a-z0-9])*|(_?[A-Z0-9])*|_)$',
        default='my_orchd_project'
    )
    namespace: str = ''
    main_package: str = 'project'
    reactions: Dict[str, str] = {}
    sensors: Dict[str, str] = {}
    sinks: Dict[str, str] = {}

    def add_reaction(self, name: str, handler: str):
        self.reactions[name] = handler

    def add_sensor(self, name: str, class_: str):
        self.sensors[name] = class_

    def add_sink(self, name: str, class_: str):
        self.sinks[name] = class_

