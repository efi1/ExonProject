import pytest
from tests import settings
from importlib.resources import files, contents
from conftest import cfg_get_data


@pytest.mark.parametrize('test_name', contents(settings.cfg_tests_dir))
def test_search_results(search_client, test_name):
    """
    The test performing a search (by given a search term) will end with the correct results and with the right order,
    in refer to rank table and the priority.
    :param search_client: the main client, which responsible for running the jobs, inserting websites and perform search
    :param cfg_data: the test's input as well as expected output data.
    :return: None. assert the expected result against the actual.
    """
    """execute tear_down:
        clean DB or delete database and then create it - depends on settings.py values:
        is_delete_and_recreate_tables, is_truncate_tables
        # also delete to_be_inserted_into_ranking.txt file if exist and if is_delete_updating_ranking_file=True
    """
    search_client.tear_down
    # insert into insert_ranking_parameters DB table.
    search_client.insert_ranking_parameters
    # insert into products job
    search_client.insert_products_job
    # insert_new_site_into_search_engine_api
    cfg_data = cfg_get_data(test_name)
    unique_url_l = [
        {"product_unique_url": search_client.insert_new_site_into_search_engine_api(website['url'], website['product'],
                                                                                    website['keywords'],
                                                                                    website['seniority'],
                                                                                    website['ref'])} for website in
                                                                                    (cfg_data['websites'])]
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
