import json

import pytest
from tests import settings
from importlib.resources import files


def load_test_params(path):
    with open(path) as file:
        data = json.loads(file.read())
    return data


def cfg_get_data(test_name: str) -> dict:
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


def preconditions_db_activities(client) -> object:
    """
    Preconditioned activities to be run (on request) before *each* test is run.
    (Truncate, Delete, Create, Insert)
    :param search_client: api client
    """
    # delete the file which uses to save websites_products.id list for updating search_engine_ranking table
    if settings.is_delete_updating_ranking_file:
        client.tear_down
    # if in settings, the tables are set to be removed
    if settings.is_delete_and_recreate_tables:
        client.delete_db_tables(settings.db_data_dir, settings.table_del_fn, force=False)
        client.create_db_tables(settings.db_data_dir, settings.table_creation_fn, force=True)
    # by default the tables are truncated for every run - can be changed in the settings module (src.tests.settings)
    elif settings.is_truncate_tables:
        deleted_tables_list = settings.tables_list.split(',')
        client.truncate_tables(deleted_tables_list)
    # if tables were removed or truncated it needed to repopulate
    if any([settings.is_delete_and_recreate_tables, settings.is_truncate_tables]):
        # insert reference data to ranking_parameters as a precondition to running the tests.
        client.insert_ranking_parameters(settings.db_data_dir, settings.rank_insert_fn, settings.rank_tn)
        # run insert process job as a precondition to running the tests.
        client.insert_products_job(settings.db_data_dir, settings.products_insert_fn, settings.products_tn)


@pytest.mark.parametrize('test_name',
                         ['test_search_results_sorted_by_priority', 'test_empty_keywords', 'test_duplicate_keywords'])
def test_search_results(search_client, test_name):
    """
    The test performing a search (by given a search term) will end with the correct results and with the right order,
    in refer to rank table and the priority.
    :param search_client: the main client, which responsible for running the jobs, inserting websites and perform search
    :param cfg_data: the test's input as well as expected output data.
    :return: None. assert the expected result against the actual.
    """

    # insert to product job has already ran during setup (see tests.contest)

    # clean DB or delete database and then create it - depends on settings.py values:
    # is_delete_and_recreate_tables, is_truncate_tables
    preconditions_db_activities(search_client)

    # insert_new_site_into_search_engine_api
    cfg_data = cfg_get_data(test_name)
    for opt_idx, website in enumerate(cfg_data['websites']):
        res = search_client.insert_new_site_into_search_engine_api(website['url'], website['product'],
                                                                   website['keywords'],
                                                                   website['seniority'], website['ref'])
        expected_url = (cfg_data['results']['insertion_results'][opt_idx]['url'])
        assert res.startswith(expected_url) == True if res else res == expected_url, \
            F"wrong unique url returned, expected: starts with {expected_url}, actual: {res}"
    # run update_ranking_job process
    res = search_client.update_ranking_job
    assert res == cfg_data['results'][
        'ranking_job_result'], F"wrong results; expected: {cfg_data['result']}, actual: {res['data']}"
    res = search_client.get_search_term_options('leisure time')
    assert res['status'] == 'success', F"Error occurred {res['data']}"
    r = search_client.validate_test_result(res, cfg_data)
    # check that unique url link is correct among the other data validation
    assert r == True, F"wrong results; expected: {cfg_data['result']}, actual: {res['data']}"
