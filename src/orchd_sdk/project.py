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

import ast
import json
import os
import shutil
import string
from string import Template

from git import Repo

from orchd_sdk import util
from orchd_sdk.models import Project


PROJECT_TEMPLATE_REPO = 'https://github.com/iiot-orchestrator/orchd-project-template.git'
PROJECT_TEMPLATE_DIR = '.orchd'
REACTION_TEMPLATE_FILE = os.path.join(PROJECT_TEMPLATE_DIR,
                                      'src/pkg_name/reactions/base_reaction.py.template')
SENSOR_TEMPLATE_FILE = os.path.join(PROJECT_TEMPLATE_DIR,
                                    'src/pkg_name/sensors/base_sensor.py.template')
SINK_TEMPLATE_FILE = os.path.join(PROJECT_TEMPLATE_DIR,
                                  'src/pkg_name/sinks/base_sink.py.template')


class ProjectBootstrapper:

    @staticmethod
    def setup_project(project: Project):
        folder_handler = ProjectFoldersHandler(project)
        folder_handler.prepare_project_folders()
        ProjectTemplateFilesHandler(project).process_templates()


class ProjectFoldersHandler:

    def __init__(self, project: Project):
        self.project = project

    def prepare_project_folders(self):
        self.clone_orchd_project_template()
        self.copy_skeleton()
        self.rename_main_package_folder()

    def copy_skeleton(self):
        shutil.copytree(self.template_dir(), self.project_dir(), dirs_exist_ok=True,
                        ignore=lambda src, names: [n for n in names if n in self.initial_ignored_files()])

    @staticmethod
    def initial_ignored_files():
        return ['base_sink.py.template', 'base_sensor.py.template', 'base_reaction.py.template']

    def rename_main_package_folder(self):
        shutil.move(f'{self.project_dir()}/src/pkg_name', f'{self.project_dir()}/src/{self.project.main_package}')

    @staticmethod
    def is_template_folder_present():
        return os.path.exists(PROJECT_TEMPLATE_DIR)

    def clone_orchd_project_template(self):
        Repo.clone_from(PROJECT_TEMPLATE_REPO, self.template_dir())
        shutil.rmtree(os.path.join(self.template_dir(), '.git'))

    def template_dir(self):
        return os.path.join(self.project_dir(), PROJECT_TEMPLATE_DIR)

    def project_dir(self):
        return os.path.join(os.getcwd(), self.project.name)


class ProjectTemplateFilesHandler:

    def __init__(self, project):
        self.project = project

    def process_templates(self):
        self.create_project_meta_file()
        self.create_version_file()
        self.create_setup_cfg_file()

    def create_project_meta_file(self):
        with open(f'{self.project.name}/orchd.meta.json', 'w') as fd:
            fd.write(json.dumps(self.project.dict(), indent=2) + '\n\n')

    def create_version_file(self):
        version_file_template = self.load_version_file_template()
        with open(f'{self.project.name}/VERSION', 'w') as version_file:
            version_file_content = string.Template(version_file_template).substitute(
                version=self.project.version
            )
            version_file.write(version_file_content + '\n\n')

    def load_version_file_template(self):
        with open(f'{self.project.name}/VERSION', 'r') as version_file:
            return version_file.read()

    def create_setup_cfg_file(self):
        setup_cfg_template = self.load_setup_cfg_template()
        with open(f'{self.project.name}/setup.cfg', 'w') as setup_cfg:
            setup_cfg_content = string.Template(setup_cfg_template).substitute(
                name=self.project.name,
                description=self.project.description,
                license=self.project.license
            )
            setup_cfg.write(setup_cfg_content + '\n\n')

    def load_setup_cfg_template(self):
        with open(f'{self.project.name}/setup.cfg', 'r') as setup_cfg_file:
            return setup_cfg_file.read()


class ReactionProperties:

    def __init__(self, project, reaction_module_name, version, triggers, sinks, handler_params, active):
        self.project = project
        self.reaction_module_name = reaction_module_name
        self.version = version
        self.triggers = triggers
        self.sinks = sinks
        self.handler_params = handler_params
        self.active = active

    def reaction_module_fq_name(self):
        return f'{self.project.main_package}.reactions.{self.reaction_module_name}'

    def reaction_class_name(self):
        return f'{util.snake_to_camel_case(self.reaction_module_name)}Reaction'

    def reaction_class_fq_name(self):
        return f'{self.reaction_module_fq_name()}.{self.reaction_class_name()}'

    def reaction_handler_class_name(self):
        return f'{self.reaction_class_name()}Handler'

    def reaction_handler_class_fq_name(self):
        return f'{self.reaction_module_fq_name()}.{self.reaction_handler_class_name()}'

    def reaction_namespaced_name(self):
        return f'{self.project.namespace}.{self.reaction_class_name()}'

    @staticmethod
    def triggers_list_from_str(triggers_str):
        try:
            triggers_as_list = ast.literal_eval(triggers_str)
            if type(triggers_as_list) is not list:
                raise ValueError(
                    'Triggers not seems to be a valid list. Use the format ["trigger1", "trigger2", "etc..."]')
            return triggers_as_list
        except ValueError:
            raise ValueError('Not able to process list of triggers. Verify its value.')


class ReactionTemplateFileHandler:

    def __init__(self, project: Project, reaction_properties: ReactionProperties):
        self.project = project
        self.reaction_properties = reaction_properties

    def create_reaction_module_file(self):
        self.copy_reaction_template_module_file()
        self.process_reaction_template()

    def copy_reaction_template_module_file(self):
        shutil.copyfile(REACTION_TEMPLATE_FILE, self.reaction_module_file_path())

    def process_reaction_template(self):
        reaction_template_str = Template(self.load_reaction_template_file())
        reaction_content = reaction_template_str.substitute(
            reaction_name=self.reaction_properties.reaction_namespaced_name(),
            reaction_class_name=self.reaction_properties.reaction_class_name(),
            reaction_handler_class_name=self.reaction_properties.reaction_handler_class_name(),
            reaction_handler_fqn_class=self.reaction_properties.reaction_handler_class_fq_name(),
            version=self.reaction_properties.version,
            triggers=self.reaction_properties.triggers,
            handler_params=self.reaction_properties.handler_params,
            active=self.reaction_properties.active,
            sinks=self.reaction_properties.sinks
        )
        self.save_reaction_file(reaction_content)

    def reaction_module_file_path(self):
        return f'./src/{self.project.main_package}/reactions/{self.reaction_properties.reaction_module_name}.py'

    def load_reaction_template_file(self):
        with open(self.reaction_module_file_path(), 'r') as reaction_template_file:
            return reaction_template_file.read()

    def save_reaction_file(self, content):
        with open(self.reaction_module_file_path(), 'w') as reaction_file:
            reaction_file.write(content)


class ReactionBootstrapper:

    @staticmethod
    def create(project: Project, reaction_properties: ReactionProperties):
        template_file_handler = ReactionTemplateFileHandler(project, reaction_properties)
        template_file_handler.create_reaction_module_file()


class SensorProperties:
    def __init__(self, project, sensor_module_name, description, version, sensor_param,
                 sensing_interval, communicator):
        self.project = project
        self.sensor_module_name = sensor_module_name
        self.description = description
        self.version = version
        self.sensor_param = sensor_param
        self.sensing_interval = sensing_interval
        self.communicator = communicator

    def sensor_namespaced_name(self):
        return f'{self.project.namespace}.{self.sensor_class_name()}'

    def sensor_module_fq_name(self):
        return f'{self.project.main_package}.sensors.{self.sensor_module_name}'

    def sensor_class_name(self):
        return util.snake_to_camel_case(self.sensor_module_name) + 'Sensor'

    def sensor_class_fq_name(self):
        return f'{self.sensor_module_fq_name()}.{self.sensor_class_name()}'


class SensorTemplateFileHandler:

    def __init__(self, project: Project, sensor_properties: SensorProperties):
        self.project = project
        self.sensor_properties = sensor_properties

    def create_sensor_module_file(self):
        self.copy_sensor_module_template_file()
        self.process_sensor_template()

    def copy_sensor_module_template_file(self):
        shutil.copy(SENSOR_TEMPLATE_FILE, self.sensor_module_file_path())

    def sensor_module_file_path(self):
        return f'./src/{self.project.main_package}/sensors/{self.sensor_properties.sensor_module_name}.py'

    def process_sensor_template(self):
        sensor_module_template = Template(self.load_sensor_template_file())
        content = sensor_module_template.substitute(
            sensor_name=self.sensor_properties.sensor_namespaced_name(),
            sensor_class_name=self.sensor_properties.sensor_class_name(),
            sensor_class_fqn=self.sensor_properties.sensor_class_fq_name(),
            communicator_class_fqn=self.sensor_properties.communicator,
            version=self.sensor_properties.version,
            description=self.sensor_properties.description,
            parameters=self.sensor_properties.sensor_param,
            sensing_interval=self.sensor_properties.sensing_interval
        )
        self.save_sensor_file(content)

    def load_sensor_template_file(self):
        with open(self.sensor_module_file_path()) as sensor_template_str:
            return sensor_template_str.read()

    def save_sensor_file(self, content):
        with open(self.sensor_module_file_path(), 'w') as sensor_file:
            sensor_file.write(content + '\n\n')


class SensorBootstrapper:

    @staticmethod
    def create(project: Project, sensor_properties: SensorProperties):
        sensor_template_handler = SensorTemplateFileHandler(project, sensor_properties)
        sensor_template_handler.create_sensor_module_file()


class SinkProperties:

    def __init__(self, project: Project, sink_module_name: str, version: str, parameters: str):
        self.project = project
        self.sink_module_name = sink_module_name
        self.version = version
        self.parameters = parameters

    def sink_class_name(self):
        return util.snake_to_camel_case(self.sink_module_name) + 'Sink'

    def sink_module_fq_name(self):
        return f'{self.project.main_package}.sinks.{self.sink_module_name}'

    def sink_class_fq_name(self):
        return f'{self.sink_module_fq_name()}.{self.sink_class_name()}'

    def sink_namespaced_name(self):
        return f'{self.project.namespace}.{self.sink_module_name}.{self.sink_class_name()}'

    def sink_json_parameters_as_dict(self):
        return json.loads(self.parameters)


class SinkTemplateFileHandler:

    def __init__(self, project: Project, sink_properties: SinkProperties):
        self.project = project
        self.sink_properties = sink_properties

    def create_sink_module_file(self):
        self.copy_sink_template_file()
        self.process_sink_template_file()

    def process_sink_template_file(self):
        template = Template(self.load_sink_module_file())
        content = template.substitute(
            sink_class_name=self.sink_properties.sink_class_name(),
            sink_class_fq_name=self.sink_properties.sink_class_fq_name(),
            sink_namespaced_name=self.sink_properties.sink_namespaced_name(),
            sink_version=self.sink_properties.version,
            sink_properties=self.sink_properties.parameters
        )
        self.save_sink_file(content)

    def save_sink_file(self, content):
        with open(self.sink_module_file_path(), 'w') as sink_module_file:
            sink_module_file.write(content + '\n\n')

    def copy_sink_template_file(self):
        shutil.copy(SINK_TEMPLATE_FILE, self.sink_module_file_path())

    def sink_module_file_path(self):
        return f'./src/{self.project.main_package}/sinks/{self.sink_properties.sink_module_name}.py'

    def load_sink_module_file(self):
        with open(self.sink_module_file_path(), 'r') as sink_module_file:
            return sink_module_file.read()


class SinkBootstrapper:

    @staticmethod
    def create(project: Project, sink_properties: SinkProperties):
        handler = SinkTemplateFileHandler(project, sink_properties)
        handler.create_sink_module_file()
