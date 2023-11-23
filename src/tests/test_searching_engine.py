

def test_search_results(search_client, cfg_data, tests_preconditions):
    """
    The test performing a search (by given a search term) will end with the correct results and with the right order,
    in refer to rank table and the priority.
    :param search_client: the main client, which responsible for running the jobs, inserting websites and perform search
    :param cfg_data: the test's input as well as expected output data.
    :return: None. assert the expected result against the actual.
    """
    # insert to product job has already ran during setup (see tests.contest)
    # insert_new_site_into_search_engine_api
    for website in cfg_data['websites']:
        search_client.insert_new_site_into_search_engine_api(website['url'], website['product'], website['keywords'],
                                                          website['seniority'], website['ref'])
    # run update_ranking_job process
    res = search_client.update_ranking_job
    assert res == cfg_data['results']['ranking_job_result'], F"wrong results; expected: {cfg_data['result']}, actual: {res['data']}"
    res = search_client.get_search_term_options('leisure time')
    assert res['status'] == 'success', F"Error occurred {res['data']}"
    assert res['data'] == cfg_data['results']['search_results'], F"wrong results; expected: {cfg_data['result']}, actual: {res['data']}"

