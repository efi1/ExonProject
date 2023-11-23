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
    db_path = files(settings.db_client_dir).joinpath(settings.db_name)
    data_jobs_path = files(settings.data_jobs_dir).joinpath(settings.data_jobs_fn)
    search_client = SearchWebsiteActivities(db_path, data_jobs_path)
    yield search_client

