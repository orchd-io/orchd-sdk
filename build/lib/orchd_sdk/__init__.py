import os

_version_file_path = os.path.join(os.path.dirname(__file__), 'VERSION')


def version():
    with open(_version_file_path) as version_file:
        return version_file.readline().strip()
