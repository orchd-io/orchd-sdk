import os
import logging.config

config_file = os.path.join(os.path.dirname(__file__), 'logger.ini')


def config():
    logging.config.fileConfig(config_file, disable_existing_loggers=False)
