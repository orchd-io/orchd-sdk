import pytest

from orchd_sdk.errors import NotFoundError, InvalidRequestError


@pytest.mark.asyncio
async def test_add_sink_template(client, sink_template):
    response = await client.sinks.add_sink_template(sink_template)
    assert response == sink_template


@pytest.mark.asyncio
async def test_add_invalid_sink_template(client, sink_template):
    sink_template.name = None
    with pytest.raises(InvalidRequestError):
        await client.sinks.add_sink_template(sink_template)


@pytest.mark.asyncio
async def test_get_sink_templates(client, sink_template):
    sinks = await client.sinks.get_sink_templates()
    current_len = len(sinks)

    await client.sinks.add_sink_template(sink_template)
    response = await client.sinks.get_sink_templates()
    assert len(response) == current_len + 1


@pytest.mark.asyncio
async def test_get_sink_template(client, sink_template):
    template = await client.sinks.add_sink_template(sink_template)
    response = await client.sinks.get_sink_template(template.id)
    assert response == template


@pytest.mark.asyncio
async def test_get_nonexistent_sink_template(client):
    with pytest.raises(NotFoundError):
        await client.sinks.get_sink_template('invalid-id')


@pytest.mark.asyncio
async def test_remove_sink_template(client, sink_template):
    template = await client.sinks.add_sink_template(sink_template)
    response = await client.sinks.remove_sink_template(template.id)
    assert response == template.id


@pytest.mark.asyncio
async def test_remove_nonexistent_sink_template(client):
    with pytest.raises(NotFoundError):
        await client.sinks.remove_sink_template('invalid-id')

