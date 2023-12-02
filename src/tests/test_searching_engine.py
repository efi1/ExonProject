import json
import pytest
from tests import settings
from importlib.resources import files, contents



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


@pytest.mark.parametrize('test_name', contents(settings.cfg_tests_dir))
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
    search_client.tear_down

    # insert_new_site_into_search_engine_api
    cfg_data = cfg_get_data(test_name)
    unique_url_l = [{"product_unique_url": search_client.insert_new_site_into_search_engine_api(website['url'], website['product'],
                                                                         website['keywords'], website['seniority'],
                                                                         website['ref'])} for opt_idx,
                                                                            website in enumerate(cfg_data['websites'])]
    r = search_client.validate_test_result({"data": unique_url_l}, cfg_data, 'insertion_results')
    # validate that the retrieved url is as expected
    assert r == True, F"wrong results; expected: {cfg_data['results']['insertion_results']}, actual: {unique_url_l}"
    res = search_client.update_ranking_job
    assert res == cfg_data['results'][
        'ranking_job_result'], F"wrong results; expected: {cfg_data['result']['search_results']}, actual: {res['data']}"
    res = search_client.get_search_term_options('leisure time', settings.db_data_dir, settings.search_query_fn)
    assert res['status'] == 'success', F"Error occurred {res['data']}"
    r = search_client.validate_test_result(res, cfg_data, 'search_results')
    # check that the search results order is correct as well as the retrieved unique url
    assert r == True, F"wrong results; expected: {cfg_data['results']['search_results']}, actual: {res['data']}"
