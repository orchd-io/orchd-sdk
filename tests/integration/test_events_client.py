import pytest


@pytest.mark.asyncio
async def test_if_event_propagation(client):
    stream = await client.events.event_stream()

    await client.events.propagate('test1', {'test1': 'test1'})
    event = await stream.next()
    assert event.event_name == 'test1'
    assert event.data == {'test1': 'test1'}

    await client.events.propagate('test2', {'test2': 'test2'})
    event = await stream.next()
    assert event.event_name == 'test2'
    assert event.data == {'test2': 'test2'}

    await stream.close()

