#!/usr/bin/env python3

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

import importlib
import json
import os
import subprocess
import sys
from time import sleep

import click

from orchd_sdk import version
from orchd_sdk.models import Project
from orchd_sdk.project import ReactionBootstrapper, ProjectBootstrapper, ReactionProperties, SensorProperties, \
    SensorBootstrapper, \
    SinkProperties, SinkBootstrapper
from orchd_sdk.util import is_snake_case, is_kebab_case

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
        fd.write(json.dumps(project.dict(), indent=2) + '\n\n')


def snake_case_validator(_, __, value):
    if is_snake_case(value):
        return value
    raise click.BadParameter('Name must be snake case. e.g "some_valid_name"')


def kebab_case_validator(_, __, value):
    if is_kebab_case(value):
        return value
    raise click.BadParameter('Name of must be kebab case. e.g "some-valid-name"')


def check_twine_is_present():
    try:
        import twine
    except ImportError:
        click.echo('Twine is required to deploy, and it is not present! '
                   'Install it with "pip install twine" and try again!')
        sys.exit(-1)


def check_current_dir_is_project_root(ctx):
    if not PROJECT and not ctx.invoked_subcommand == 'project':
        print('Error! Be sure to be in a orchd-sdk project root!')
        sys.exit(-1)


def echo_operation_result(operation: str, result: bool):
    click.secho(operation + '... ', bold=True, nl=False)
    if result:
        click.secho('OK!', fg='green')
    else:
        click.secho(' FAILED!', fg='red')
    sleep(1)


def echo_warning(message: str):
    click.secho('WARNING... ', bold=True, nl=False)
    click.secho(message, fg='yellow')
    sleep(1)


def run_shell_command(parameters, cmd_display_name, exit_on_error=True, error_msg='Error. Aborting!'):
    result = subprocess.run(parameters)
    echo_operation_result(cmd_display_name, not bool(result.returncode))
    if result.returncode != 0 and exit_on_error:
        click.echo(error_msg)
        sys.exit(-1)


@click.group()
def actions_group():
    pass


@actions_group.command('template')
@click.option('--from', 'from_', required=True)
def generate_template(from_):
    """Generate a template from an Orchd Asset."""
    split_name = from_.split('.')
    module = '.'.join(split_name[:-1])
    class_name = split_name[-1]
    try:
        Class = getattr(importlib.import_module(module), class_name)
        click.echo(Class.template.json(indent=2))
    except ModuleNotFoundError as e:
        click.echo(f'{e}! Is the related package installed? Try "pip install the_package_containing_module"')
    except AttributeError as e:
        click.echo(f'Module {module} seems not to have a class named {class_name}')


@click.group()
def new_actions_group():
    pass


@new_actions_group.command('reaction')
@click.option('--name', '-n', 'reaction_module_name', callback=snake_case_validator, prompt="Reaction module name (use snake case)")
@click.option('--version', '-v', prompt='Reaction version')
@click.option('--triggers', '-t', prompt='List of event triggers (ex. '
                                         '["io.orchd.events.system.Test", "com.example.events.SomeEvent2"])',
              )
@click.option('--handler_params', '-hp', prompt='Handler parameters (json format)')
@click.option('--active', '-a', default=True, prompt='Active reaction after load?', type=click.types.BOOL)
def new_reaction(reaction_module_name, version, triggers, handler_params, active):
    """Creates a new Reaction"""
    global PROJECT
    handler_params = handler_params or {}
    triggers = triggers or '[]'
    sinks = []

    click.echo('Setting up reaction...')

    reaction_properties = ReactionProperties(PROJECT, reaction_module_name,
                                             version, triggers, sinks,
                                             handler_params, active)
    ReactionBootstrapper.create(PROJECT, reaction_properties)

    PROJECT.add_reaction(reaction_properties.reaction_namespaced_name(),
                         reaction_properties.reaction_class_fq_name())
    save_project(PROJECT)

    click.echo('Done!')


@new_actions_group.command('sensor')
@click.option('--name', '-n', 'sensor_module_name', callback=snake_case_validator,
              help='Sensor module name (use snake case)', prompt='Sensor module name (use snake case)')
@click.option('--description', '-d', default='', help='Brief description for the new sensor.',
              prompt='Brief description of the Sensor', show_default=True)
@click.option('--version', '-v', default='0.0', help='Version number for the sensor.',
              prompt='Sensor version', show_default=True)
@click.option('--sensor-param', '-sp', help='Sensor Parameters as JSON',
              prompt='Sensor parameters as JSON')
@click.option('--sensing-interval', '-si', default=1, help='Sensing Interval in seconds (int)', type=click.INT,
              prompt='Sensing interval', show_default=True)
@click.option('--communicator', '-c', default='orchd_sdk.sensor.LocalCommunicator',
              show_default=True)
def new_sensor(sensor_module_name, description, version, sensor_param, sensing_interval, communicator):
    """Creates a new sensor."""
    click.echo('Setting up new Sensor...')
    sensor_properties = SensorProperties(PROJECT, sensor_module_name,
                                         description, version, sensor_param,
                                         sensing_interval, communicator)
    SensorBootstrapper.create(PROJECT, sensor_properties)

    PROJECT.add_sensor(sensor_properties.sensor_namespaced_name(),
                       sensor_properties.sensor_class_fq_name())
    save_project(PROJECT)
    click.echo('Done!')


@new_actions_group.command('sink')
@click.option('--name', '-n', callback=snake_case_validator, help='Name of the Sink module. (snake case)',
              prompt='Name of the Sink module (snake case)')
@click.option('--version', '-v', help='Sink version', prompt='Sink Version')
@click.option('--parameters', '-p', help='sink parameters', prompt='Sink Parameters (JSON Format)')
def new_sink(name, version, parameters):
    """Creates a new sensor"""
    sink_properties = SinkProperties(PROJECT, name, version, parameters)
    SinkBootstrapper.create(PROJECT, sink_properties)
    PROJECT.add_sink(sink_properties.sink_namespaced_name(), sink_properties.sink_class_name())
    save_project(PROJECT)

    click.echo('SUCCESS!')
    click.echo(f'Sink name is: {sink_properties.sink_namespaced_name()}')
    click.echo(f'Sink module created as: {sink_properties.sink_module_fq_name()}')
    click.echo(f'Sink class reference is: {sink_properties.sink_class_fq_name()}')


@new_actions_group.command('project')
@click.option('--name', '-n', callback=kebab_case_validator, help='Name of the project', prompt='Give a name for the project')
@click.option('--namespace', '-ns', help='Project namespace', prompt='Give the project a namespace (ex. com.example)')
@click.option('--author', '-a', help='Project author', prompt='Project author\'s name')
@click.option('--license', '-l', help='Project license', prompt='Project\'s license')
@click.option('--version', '-v', help='Version of the Project', prompt='Project version')
@click.option('--description', '-d', help='Project description', prompt='Project description')
def new_project(**kwargs):
    """Create a new Project"""
    global PROJECT
    if not PROJECT and not os.path.exists(f'./{kwargs.get("name")}'):
        PROJECT = Project(**kwargs)
        ProjectBootstrapper.setup_project(PROJECT)
    else:
        click.echo('Not able to create the project. A project already exists with this name or in this directory.')


@actions_group.command('test')
def test():
    """Run project tests"""
    run_shell_command(['pytest', '-q'], cmd_display_name='TESTS')


@actions_group.command('build')
@click.option('--skip-tests', help='Skip tests.', is_flag=True)
@click.pass_context
def build(ctx, skip_tests):
    """Build the project and generates the packages"""
    if not skip_tests:
        ctx.invoke(test)

    run_shell_command(['python', 'setup.py', 'sdist', 'bdist_wheel'], cmd_display_name='BUILD',
                      error_msg='Error, Not able to build.')


@actions_group.command('deploy')
@click.option('--upload', help='Deploy definitely the package.', is_flag=True)
@click.option('--skip-tests', help='Skip tests', is_flag=True)
@click.pass_context
def deploy(ctx, upload, skip_tests):
    """Deploy your project to PyPi"""
    check_twine_is_present()
    ctx.invoke(build, skip_tests=skip_tests)
    upload_package_to_pypi(upload)


def upload_package_to_pypi(test_upload=False):
    if test_upload:
        run_shell_command(['twine', 'upload'], cmd_display_name='UPLOAD')
    else:
        upload_package_test()


def upload_package_test():
    click.echo('We will do a test at PyPi Test Server (https://test.pypi.org) '
               'before uploading to PyPi. You need an account there. YOUR PyPi '
               'CREDENTIALS will not work.')
    click.confirm('Are you ready to proceed?', abort=True)
    run_shell_command(['twine', 'upload', '--skip-existing', '-r', 'testpypi', './dist/*'],
                      cmd_display_name='UPLOAD TEST')
    echo_warning('Package was not Upload to production Server yet! (testpypi)!')
    click.echo('Go to test.pypi.org and verify the package.')
    click.secho('To deploy to PyPi run "orchd-sdk deploy --upload"', bold=True)


@actions_group.command(cls=click.CommandCollection, sources=[new_actions_group])
@click.pass_context
def new(ctx):
    """Create new Orchd Assets (Reactions, Sensors, Sinks)"""
    check_current_dir_is_project_root(ctx)


@click.group(cls=click.CommandCollection, sources=[actions_group])
@click.version_option(version())
@click.pass_context
def cli(ctx):
    pass
