"""Shared fixtures."""
import json
import os  # being used in func: pytest_addoption
from pathlib import Path

from pytest import fixture
from tests import settings
from src.utils.utils import dict_to_obj, obj
from src.clients.api_tests_client import TestsClient
from src.clients.selen_tests_client import SelenTestsClient
from jinja2 import Environment, FileSystemLoader

# get all global settings for running the tests
# settings_items = [i for i in settings.__dir__() if not i.startswith('_')]
with open(eval(settings.cfg_global_file), "r+") as global_cfg:
    GLOBAL = json.loads(global_cfg.read())


def pytest_addoption(parser):
    #   creating execution Pytest flags by a given settings file
    for key, value in GLOBAL.items():
        try:
            value = eval(value)
        except (SyntaxError, NameError, TypeError, ZeroDivisionError):
            pass
        parser.addoption(F"--{key}", action='store', default=value)


@fixture(scope="function")
def test_name(request):
    return request.node.name


@fixture(scope="session")
def tests_raw_data(request: object) -> dict:
    """
    creating a dict data set with all the available flags and their default values
    :param request: a pytest object
    :return: a dict with all settings items
    """
    raw_data = dict()
    for item in GLOBAL:
        raw_data[item] = request.config.getoption(F"--{item}")
    return raw_data


@fixture(scope="session")
def settings_data(tests_raw_data: dict) -> object:
    """
    Converting raw data of type dict to an object
    :param tests_raw_data: raw data input
    :return:
    """
    return dict_to_obj(tests_raw_data)


@fixture(scope="function")
def cfg_data(tests_raw_data: dict, test_name: str) -> dict:
    """
    Rendering config data out of a template cfg file
    :param test_name:
    :param tests_raw_data: data to be rendered with in the cfg template file
    :param cfg_name: cfg file name
    :param cfg_dir: cfg folder path
    :return: dict with the rendered data
    """
    cfg_name = F'{test_name}.cfg'
    cfg_template_dir = eval(settings.cfg_tests_folder)
    cfg_template_file = Path(cfg_template_dir).joinpath(cfg_name)
    if cfg_template_file.exists():
        template_loader = FileSystemLoader(searchpath=cfg_template_dir)
        template_env = Environment(loader=template_loader)
        template = template_env.get_template(cfg_name)
        cur = dict(tests_raw_data.items())
        cfg_data_str = template.render(cur)
        cfg_data_dict = json.load(cfg_data_str)
        return dict_to_obj(cfg_data_dict)


@fixture(scope="session")
def selen_tests_client(settings_data: object) -> object:
    """
    instantiate the selen_tests_client
    :param settings_data: global data arguments
    :return: client instant
    """
    selen_tests_client = SelenTestsClient(settings_data)
    selen_tests_client.open_page
    yield selen_tests_client
    selen_tests_client.client_tear_down


@fixture(scope="session")
def api_tests_client(settings_data: object) -> object:
    """
    instantiate the api_tests_client
    :param settings_data: global data arguments
    :return: client instant
    """
    yield TestsClient(settings_data)
