from string import Template

from orchd_sdk.models import ReactionTemplate


def process_reaction_skeleton(file, template: ReactionTemplate):
    with open(file, 'r') as fd:
        template_string = Template(fd.read())
        new_content = template_string.substitute(
            reaction_name=template.name,
            reaction_class_name=template.name.split('.')[-1],
            reaction_handler_class_name=template.handler.split('.')[-1],
            reaction_handler_fqn_class=template.handler,
            version=template.version,
            triggers=template.triggered_on,
            handler_params=template.handler_parameters,
            active=template.active,
            sinks=template.sinks
        )

    with open(file, 'w') as fd:
        fd.write(new_content)


def process_reaction_template():
    pass
