import pytest

from orchd_sdk.errors import NotFoundError, InvalidRequestError
from orchd_sdk.sink import DummySink



@pytest.mark.asyncio
async def test_get_reactions(client):
    response = await client.reactions.get_reactions()
    assert type(response) == list


@pytest.mark.asyncio
async def test_add_reaction(client, reaction_template):
    template = reaction_template
    await client.reactions.add_reaction_template(template)

    response = await client.reactions.add_reaction(template.id)
    assert response.template.id == template.id


@pytest.mark.asyncio
async def test_add_reaction_from_nonexistent_template(client):
    with pytest.raises(NotFoundError):
        await client.reactions.add_reaction(template_id='invalid-id')


@pytest.mark.asyncio
async def test_get_reaction(client, reaction_template):
    reaction_template = await client.reactions.add_reaction_template(reaction_template)
    reaction = await client.reactions.add_reaction(reaction_template.id)

    response = await client.reactions.get_reaction(reaction.id)
    assert reaction.id == response.id


@pytest.mark.asyncio
async def test_add_reaction_template(client, reaction_template):
    template = reaction_template
    response = await client.reactions.add_reaction_template(template)
    assert response == template


@pytest.mark.asyncio
async def test_add_invalid_reaction_template(client, reaction_template):
    template = reaction_template
    template.name = None
    with pytest.raises(InvalidRequestError):
        await client.reactions.add_reaction_template(template)


@pytest.mark.asyncio
async def test_remove_reaction(client, reaction_template):
    template = await client.reactions.add_reaction_template(reaction_template)
    reaction = await client.reactions.add_reaction(template.id)
    response = await client.reactions.remove_reaction(reaction.id)
    assert response == reaction.id


@pytest.mark.asyncio
async def test_remove_nonexistent_reaction(client):
    with pytest.raises(NotFoundError):
        await client.reactions.remove_reaction('invalid-id')


@pytest.mark.asyncio
async def test_remove_reaction_template(client, reaction_template):
    template = await client.reactions.add_reaction_template(reaction_template)
    response = await client.reactions.remove_reaction_template(template.id)
    assert response == template.id


@pytest.mark.asyncio
async def test_remove_nonexistent_reaction_template(client):
    with pytest.raises(NotFoundError):
        await client.reactions.remove_reaction_template('invalid-id')


@pytest.mark.asyncio
async def test_get_reaction_templates(client, reaction_template):
    reactions = await client.reactions.get_reaction_templates()
    initial_len = len(reactions)

    await client.reactions.add_reaction_template(reaction_template)

    reactions = await client.reactions.get_reaction_templates()
    assert len(reactions) == initial_len + 1


@pytest.mark.asyncio
async def test_get_reaction_template(client, reaction_template):
    template = await client.reactions.add_reaction_template(reaction_template)
    response = await client.reactions.get_reaction_template(template.id)
    assert response == template


@pytest.mark.asyncio
async def test_get_nonexistent_reaction_template(client):
    with pytest.raises(NotFoundError):
        await client.reactions.get_reaction_template('invalid-id')


@pytest.mark.asyncio
async def test_add_sink_to_reaction(client, reaction_template, sink_template):
    reaction_template.sinks = []

    template = await client.reactions.add_reaction_template(reaction_template)
    reaction = await client.reactions.add_reaction(template.id)

    sink_template = await client.sinks.add_sink_template(sink_template)

    await client.reactions.add_sink_to_reaction(reaction.id, sink_template.id)
    reaction = await client.reactions.get_reaction(reaction.id)
    assert reaction.sinks_instances[0].template.id == sink_template.id


@pytest.mark.asyncio
async def test_add_sink_to_nonexistent_reaction(client, sink_template):
    sink_template = await client.sinks.add_sink_template(sink_template)
    with pytest.raises(NotFoundError):
        await client.reactions.add_sink_to_reaction('invalid-id', sink_template.id)


@pytest.mark.asyncio
async def test_add_sink_from_nonexistent_sink_template_to_reaction(client, reaction_template):
    reaction_template.sinks = []

    template = await client.reactions.add_reaction_template(reaction_template)
    reaction = await client.reactions.add_reaction(template.id)

    with pytest.raises(NotFoundError):
        await client.reactions.add_sink_to_reaction(reaction.id, 'invalid-id')


@pytest.mark.asyncio
async def test_remove_sink_from_reaction(client, reaction_template, sink_template):
    reaction_template.sinks = []

    template = await client.reactions.add_reaction_template(reaction_template)
    reaction = await client.reactions.add_reaction(template.id)

    sink_template = await client.sinks.add_sink_template(sink_template)
    await client.reactions.add_sink_to_reaction(reaction.id, sink_template.id)

    reaction = await client.reactions.get_reaction(reaction.id)
    sink_id = reaction.sinks_instances[0].id

    await client.reactions.remove_sink_from_reaction(reaction.id, sink_id)
    reaction = await client.reactions.get_reaction(reaction.id)
    assert len(reaction.sinks_instances) == 0


@pytest.mark.asyncio
async def test_remove_sink_from_nonexistent_reaction(client):
    with pytest.raises(NotFoundError):
        await client.reactions.remove_sink_from_reaction('invalid-id', 'some-sink-id')


@pytest.mark.asyncio
async def test_remove_nonexistent_sink_from_reaction(client, reaction_template):
    reaction_template.sinks = []

    template = await client.reactions.add_reaction_template(reaction_template)
    reaction = await client.reactions.add_reaction(template.id)

    with pytest.raises(NotFoundError):
        await client.reactions.remove_sink_from_reaction(reaction.id, 'invalid-id')
