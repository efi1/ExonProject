import pytest
from tests import settings
from importlib.resources import contents
from conftest import cfg_get_data


@pytest.mark.parametrize('test_name',contents(settings.cfg_tests_dir)) #  ['test_empty_keywords.json'])
def test_search_results(test_client, test_name):
    """
    The test performing a search (by given a search term) will end with the correct results and with the right order,
    in refer to rank table and the priority.
    :param search_client: the main client, which responsible for running the jobs, inserting websites and perform search
    :param cfg_data: the test's input as well as expected output data.
    :return: None. assert the expected result against the actual.
    """
    """execute tear_down:
        clean DB or delete database and then create it - depends on settings.py values:
        is_delete_tables, is_truncate_tables
        # also delete to_be_inserted_into_ranking.txt file if exist and if is_delete_updating_ranking_file=True
    """
    test_client.insert_products_job()
    # insert_new_site_into_search_engine_api
    cfg_data = cfg_get_data(test_name)
    unique_url_l = [
        {"product_unique_url": test_client.insert_new_site_into_search_engine_api(website['url'], website['product'],
                                                                                  website['keywords'],
                                                                                  website['seniority'],
                                                                                  website['ref'])} for website in
        (cfg_data['websites'])]
    r = test_client.validate_test_result({"data": unique_url_l}, cfg_data, 'insertion_results')
    # validate that the retrieved url is as expected
    assert r is True, F"wrong results; expected: {cfg_data['results']['insertion_results']}, actual: {unique_url_l}"
    # to be run only if the former assertion completed successfully
    res = test_client.update_ranking_job()
    assert res == cfg_data['results'][
        'ranking_job_result'], F"wrong results; expected: {cfg_data['results']['ranking_job_result']}, actual: {res['data']}"
    res = test_client.get_search_term_options('leisure time')
    assert res['status'] == 'success', F"Error occurred {res['data']}"
    r = test_client.validate_test_result(res, cfg_data, 'search_results')
    # check that the search results order is correct as well as the retrieved unique url
    assert r is True, F"wrong results; expected: {cfg_data['results']['search_results']}, actual: {res['data']}"
