"""Shared fixtures."""
import json
from importlib.resources import files
from pytest import fixture
from tests import settings
from clients.api.search_web_activities import SearchWebsiteActivities


@fixture(scope="function")
def test_name(request):
    return request.node.name


def load_test_params(path):
    with open(path) as file:
        data = json.loads(file.read())
    return data


@fixture(scope="function")
def cfg_data(test_name: str) -> dict:
    """
    Rendering config data out of a template cfg file
    :param test_name:
    :param tests_raw_data: data to be rendered with in the cfg template file
    :return: dict test's data
    """
    cfg_name = F'{test_name}.json'
    cfg_template_dir = settings.cfg_tests_dir
    cfg_template_file = files(cfg_template_dir).joinpath(cfg_name)
    if cfg_template_file.exists():
        return load_test_params(cfg_template_file)


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


@fixture(scope="function")
def tests_preconditions(search_client) -> object:
    """
    Preconditioned activities to be run (on request) before *each* test is run.
    (Truncate, Delete, Create, Insert)
    :param search_client: api client
    """
    # delete the file which uses to save websites_products.id list for updating search_engine_ranking table
    search_client.tear_down
    # if in settings, the tables are set to be removed
    if settings.is_delete_and_recreate_tables == True:
        search_client.delete_db_tables(settings.db_data_dir, settings.table_del_fn, force=False)
        search_client.create_db_tables(settings.db_data_dir, settings.table_creation_fn, force=True)
    # by default the table are truncated for every run - can be changed in the settings module (src.tests.settings)
    elif settings.is_truncate_tables == True:
        deleted_tables_list = settings.table_list.split(',')
        search_client.truncate_tables(deleted_tables_list)
    # if tables were removed or truncated it needed to repopulate
    if any([settings.is_delete_and_recreate_tables, settings.is_truncate_tables]):
        # insert refernce data to ranking_parameters as a precondition to running the tests.
        search_client.insert_ranking_parameters(settings.db_data_dir, settings.rank_insert_fn, settings.rank_tn)
        # run insert process job as a precondition to running the tests.
        search_client.insert_products_job(settings.db_data_dir, settings.products_insert_fn, settings.products_tn)