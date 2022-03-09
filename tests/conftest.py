import pytest

from orchd_sdk.models import SensorTemplate, Sensor, SinkTemplate, Sink, \
    ReactionTemplate, ReactionInfo
from orchd_sdk.reaction import ReactionsEventBus
from orchd_sdk.sensor import DummySensor, SensorState


@pytest.fixture()
def reaction_event_bus():
    yield ReactionsEventBus()


@pytest.fixture
def sink_templates_list():
    return [
        SinkTemplate(id='3001', name='io.orchd.examples.SinkToHttpService',
                     version='1.0', sink_class='orchd_sinks.http.HTTPJsonSink',
                     properties={
                         'method': 'POST',
                         'endpoint': 'https://example.com/test',
                         'content': b'{"some", "json"}'
                     }),
        SinkTemplate(id='3002', name='io.orchd.examples.SinkToHttpFile', version='1.0',
                     sink_class='orchd_sinks.file.FileSink',
                     properties={
                         'path': '/tmp/file',
                         'append': True,
                         'create': True,
                         'content': 'some data to sink.'
                     }),
        SinkTemplate(id='3003', name='io.orchd.examples.SinkToGraphite', version='1.0',
                     sink_class='orchd_sinks.monitoring.GraphiteSink',
                     properties={
                         'endpoint': '127.0.0.1',
                         'port': '2004',
                         'send_method': 'Pickle'
                     })

    ]


@pytest.fixture
def serialized_sinks_list(sink_templates_list):
    return [
        Sink(id='4001', template=sink_templates_list[0]),
        Sink(id='4002', template=sink_templates_list[1]),
        Sink(id='4003', template=sink_templates_list[2])
    ]


@pytest.fixture
def sensors_list():
    return [
        Sensor(
            id='2001', template=DummySensor.template, status=SensorState.RUNNING,
            events_count=5, events_forwarded=8, events_discarded=10
        ),
        Sensor(
            id='2002', template=DummySensor.template, status=SensorState.RUNNING,
            events_count=5, events_forwarded=8, events_discarded=10
        ),
        Sensor(
            id='2003', template=DummySensor.template, status=SensorState.RUNNING,
            events_count=5, events_forwarded=8, events_discarded=10
        ),
        Sensor(
            id='2004', template=DummySensor.template, status=SensorState.RUNNING,
            events_count=5, events_forwarded=8, events_discarded=10
        )

    ]


@pytest.fixture
def sensors_templates_list():
    return [
        SensorTemplate(
            id='1001', name='io.orchd.template.SensorTemplateExample1', version='1.0',
            description='SensorTemplate1 for testing purposes.',
            sensor='io.orchd.sensor.DummySensor', sensing_interval=5,
            communicator='orchd_sdk.sensor.LocalCommunicator',
            parameteres={'attribute1': 4}
        ),
        SensorTemplate(
            id='1002', name='io.orchd.template.SensorTemplateExample2', version='2.0',
            description='SensorTemplate2 for testing purposes.',
            sensor='io.orchd.sensor.DummySensor', sensing_interval=1,
            communicator='orchd_sdk.sensor.LocalCommunicator'
        ),
        SensorTemplate(
            id='1003', name='io.orchd.template.SensorTemplateExample3', version='3.0',
            description='SensorTemplate3 for testing purposes.',
            sensor='io.orchd.sensor.DummySensor', sensing_interval=0.5,
            communicator='orchd_sdk.sensor.LocalCommunicator',
            parameteres={'speed': 4}
        ),
        SensorTemplate(
            id='1004', name='io.orchd.template.SensorTemplateExample4', version='4.0',
            description='SensorTemplate4 for testing purposes.',
            sensor='io.orchd.sensor.DummySensor', sensing_interval=0.1,
            communicator='orchd_sdk.sensor.LocalCommunicator',
            parameteres={'color': 'white'}
        )
    ]


@pytest.fixture
def reactions_templates_list(sink_templates_list):
    return [
        ReactionTemplate(name='io.orchd_reactions.templates.docker.ContainerReaction',
                         version='1.0', active=True, id='4001',
                         handler='orchd_reactions.docker.ContainerReaction',
                         triggered_on=[
                             'io.orchd.events.docker.ContainerCreated',
                             'io.orchd.events.docker.ContainerStopped',
                             'io.orchd.events.docker.ContainerStarted'
                         ],
                         handler_parameters={
                            'labels': ['orchd']
                         },
                         sinks=[sink_templates_list[0]]
                         ),
        ReactionTemplate(name='io.orchd_reactions.templates.mqtt.TemSensorMQTTReaction',
                         version='1.2', activate=True, id='4002',
                         handler='orchd_reactions.mqtt.MQTTEventReaction',
                         triggered_on=['io.orchd.events.mqtt.Event'],
                         handler_parameters={
                             'topics': ['orchd.event']
                         },
                         sinks=[sink_templates_list[1]]),
        ReactionTemplate(name='io.orchd_reactions.templates.mqtt.NetworkEventReaction',
                         version='2.0', activate=True, id='4003',
                         handler='orchd_reactions.dbus.DBUSEventReaction',
                         triggered_on=['io.orchd.events.dbus.Event'],
                         handler_parameters={
                             'signals': ['org.freedesktop.NetworkManager.DeviceAdded',
                                         'org.freedesktop.NetworkManager.DeviceRemoved',
                                         'org.freedesktop.NetworkManager'
                                         '.PropertiesChanged']
                         },
                         sinks=[sink_templates_list[2]]),
    ]


@pytest.fixture
def reactions_list(reactions_templates_list, serialized_sinks_list):
    return [
        ReactionInfo(
            id='5001', template=reactions_templates_list[0], state='RUNNING',
            sink_instances=[serialized_sinks_list[0], serialized_sinks_list[1]]
        ),
        ReactionInfo(
            id='5002', template=reactions_templates_list[1], state='READY',
            sink_instances=[serialized_sinks_list[2]]
        ),
        ReactionInfo(
            id='5003', template=reactions_templates_list[2], state='STOPPED',
            sink_instances=[serialized_sinks_list[0], serialized_sinks_list[1]]
        ),
        ReactionInfo(
            id='5004', template=reactions_templates_list[0], state='RUNNING',
            sink_instances=[]
        ),
        ReactionInfo(
            id='5005', template=reactions_templates_list[0], state='RUNNING'
        )
    ]
