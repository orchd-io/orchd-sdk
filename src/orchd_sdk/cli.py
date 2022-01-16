#!/usr/bin/env python3
import importlib
import json
import os
import ast
import shutil
import string
import sys
import click

from orchd_sdk.util import snake_to_camel_case, is_snake_case
from orchd_sdk.models import Project, ReactionTemplate
from orchd_sdk.skeleton import process_reaction_skeleton


REACTION_SKELETON_REPO = 'https://github.com/iiot-orchestrator/orchd-reaction-skeleton.git'
PROJECT = None

try:
    with open('orchd.meta.json') as fd:
        PROJECT = Project(**json.load(fd))
except FileNotFoundError as e:
    PROJECT = False
except json.JSONDecodeError:
    click.echo("Project file malformed.")
    sys.exit(-1)


def save_project(project: Project):
    with open(f'orchd.meta.json', 'w') as fd:
        fd.write(json.dumps(project.dict(), indent=2))


def snake_case_validator(_, __, value):
    if is_snake_case(value):
        return value
    raise click.BadParameter('Name must be snake case. e.g "some_valid_name"')


@click.group()
def actions_group():
    pass


@actions_group.command('template')
@click.option('--from', 'from_')
def generate_template(from_):
    split_name = from_.split('.')
    module = '.'.join(split_name[:-1])
    class_name = split_name[-1]

    Class = getattr(importlib.import_module(module), class_name)
    click.echo(Class.template.json(indent=2))


@click.group()
def new_actions_group():
    pass


@new_actions_group.command('reaction')
@click.option('--name', '-n', callback=snake_case_validator, prompt="Reaction Name (use snake case)")
@click.option('--version', '-v', prompt='Reaction version')
@click.option('--triggers', '-t', prompt='List of event triggers (ex. '
                                         '["io.orchd.events.system.Test", "com.example.events.SomeEvent2"])',
              )
@click.option('--handler_params', '-hp', prompt='Handler parameters (json format)')
@click.option('--active', '-a', default=True, prompt='Active reaction after load?', type=click.types.BOOL)
def new_reaction(name, version, triggers, handler_params, active):
    global PROJECT

    handler_params = handler_params or {}
    triggers = triggers or []

    reaction_module_name = name.replace('-', '_')
    reaction_module_fqn = f'{PROJECT.main_package}' \
                          f'.reactions.{reaction_module_name}'

    reaction_class_name = snake_to_camel_case(name)
    reaction_class_fqn = f'{reaction_module_fqn}.{reaction_class_name}'
    reaction_handler_class_name = f'{reaction_class_name}Handler'
    reaction_handler_fqn_class = f'{reaction_module_fqn}.{reaction_handler_class_name}'

    namespaced_reaction_template_name = f'{PROJECT.namespace}.{reaction_class_name}'

    triggers_as_array = ast.literal_eval(triggers.strip())
    if type(triggers_as_array) is not list:
        click.echo('Triggers not seems to be a valid list. Use the format ["trigger1", "trigger2", "etc..."]')
        sys.exit(-1)

    template = ReactionTemplate(name=namespaced_reaction_template_name,
                                version=version,
                                triggered_on=triggers_as_array,
                                handler=reaction_handler_fqn_class,
                                handler_params=handler_params,
                                sinks=list(), active=active)

    template_file = os.path.join(os.path.dirname(__file__),
                                 'templates/reaction/base_reaction.py.template')

    reaction_file_path = f'./src/{PROJECT.main_package}/reactions/{name}.py'
    shutil.copyfile(template_file, reaction_file_path)
    click.echo('Set up reaction...')
    process_reaction_skeleton(reaction_file_path, template)

    PROJECT.add_reaction(namespaced_reaction_template_name, reaction_class_fqn)
    save_project(PROJECT)


@new_actions_group.command('project')
@click.option('--name', '-n', help='Name of the project', prompt='Give a name for the project')
@click.option('--namespace', '-ns', help='Project namespace', prompt='Give the project a namespace (ex. com.example)')
@click.option('--author', '-a', help='Project author', prompt='Project author\'s name')
@click.option('--license', '-l', help='Project license', prompt='Project\'s license')
@click.option('--version', '-v', help='Version of the Project', prompt='Project version')
@click.option('--description', '-d', help='Project description', prompt='Project description')
def new_project(name, namespace, author, license, version, description):
    global PROJECT
    if not PROJECT and not os.path.exists(f'./{name}'):
        PROJECT = Project(
            name=name,
            namespace=namespace,
            description=description,
            author=author,
            license=license,
            version=version,
            main_package=name.replace("-", "_")
        )
        shutil.copytree(os.path.join(os.path.dirname(__file__), 'templates/project'),
                        f'./{PROJECT.name}')

        shutil.move(f'./{PROJECT.name}/src/pkg_name', f'./{PROJECT.name}/src/{PROJECT.main_package}')

        with open(f'{name}/orchd.meta.json', 'w') as fd:
            fd.write(json.dumps(PROJECT.dict(), indent=2))

        with open(f'{PROJECT.name}/VERSION', 'r') as version_file, \
             open(f'{PROJECT.name}/setup.cfg', 'r') as setup_cfg_file:
            setup_cfg_template = string.Template(setup_cfg_file.read()).substitute(
                name=name,
                description=description
            )
            version_template = string.Template(version_file.read()).substitute(
                version=version
            )

        with open(f'{PROJECT.name}/VERSION', 'w') as version, \
             open(f'{PROJECT.name}/setup.cfg', 'w') as setup_cfg:
            version.write(version_template)
            setup_cfg.write(setup_cfg_template)
    else:
        click.echo('Not able to create the project. A project already exists with this name or in this directory.')


@actions_group.command(cls=click.CommandCollection, sources=[new_actions_group])
@click.pass_context
def new(ctx):
    if not PROJECT and not ctx.invoked_subcommand == 'project':
        print('Error! Be sure to be in the Project root!')
        sys.exit(-1)
    pass


@click.group(cls=click.CommandCollection, sources=[actions_group])
@click.pass_context
def cli(ctx):
    pass

