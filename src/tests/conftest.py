"""Shared fixtures."""
import json
from importlib.resources import files
from pytest import fixture
from tests import settings
from clients.api.search_web_activities import SearchWebsiteActivities


@fixture(scope="session")
def search_client() -> object:
    """
    instantiate the search_client
    :return: client instant
    """
    search_client = SearchWebsiteActivities(**vars(settings))
    yield search_client


def cfg_get_data(test_name: str) -> dict:
    """
    Rendering config data out of a template cfg file
    :param test_name:
    :param tests_raw_data: data to be rendered with in the cfg template file
    :return: dict test's data
    """
    def _load_test_params(path):
        with open(path) as file:
            data = json.loads(file.read())
        return data
    cfg_template_dir = settings.cfg_tests_dir
    cfg_template_file = files(cfg_template_dir).joinpath(test_name)
    if cfg_template_file.exists():
        return _load_test_params(cfg_template_file)

