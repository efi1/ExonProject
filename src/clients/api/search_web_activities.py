import os
import logging
import secrets
import sys
from importlib.resources import files
from importlib.resources import read_text
from clients.db.data_base_client import DataBaseClient

logging.getLogger()


class SearchWebsiteActivities(DataBaseClient):
    def __init__(self, **kwargs):
        db_path = files(kwargs['db_client_dir']).joinpath(kwargs['db_name'])
        super().__init__(db_path)
        self.db_data_dir = kwargs['db_data_dir']
        self.table_del_fn = kwargs['table_del_fn']
        self.table_creation_fn = kwargs['table_creation_fn']
        self.products_tn = kwargs['products_tn']
        self.products_insert_fn = kwargs['products_insert_fn']
        self.rank_insert_fn = kwargs['rank_insert_fn']
        self.rank_tn = kwargs['rank_tn']
        self.data_jobs_fn = kwargs['data_jobs_fn']
        self.tables_list = kwargs['tables_list']
        self.is_delete_updating_ranking_file = kwargs['is_delete_updating_ranking_file']
        self.is_delete_and_recreate_tables = kwargs['is_delete_and_recreate_tables']
        self.is_truncate_tables = kwargs['is_truncate_tables']
        self.data_jobs_path = files(kwargs['db_client_dir']).joinpath(self.data_jobs_fn)


    def delete_db_tables(self, json_dir: str, json_fn: str,
                         force: bool = False) -> object:
        """
        deletes DB tables
        :param json_dir: json folder location
        :param json_fn: data file name
        :param force: to delete if tables exist
        :return: an object with data that contains the number of exist tables
        """
        logging.info(f'{sys._getframe().f_code.co_name} started')
        res = self.count_tables()
        logging.info(F"number of table at starting point: {res} table/s already exist")
        if force or res.data > 0:
            self.exec_sql_queries(json_dir=json_dir, json_fn=json_fn, fetch_all=False)
            res = self.count_tables()
            logging.info(F"after table deletion: {res} table/s already exist")
        logging.info(f'{sys._getframe().f_code.co_name} finished successfully')
        return res

    def create_db_tables(self, json_dir: str, json_fn: str,
                         force: bool = False) -> object:
        """
        create DB tables
        :param json_dir: json folder location
        :param json_fn: data file name
        :param force: to create also if already exist
        :return: an object with data that contains the number of created tables
        """
        logging.info(f'{sys._getframe().f_code.co_name} started')
        res = self.count_tables()
        logging.info(F"number of table at starting point: {res} table/s already exist")
        if force or res.data == 0:
            self.exec_sql_queries(json_fn=json_fn, json_dir=json_dir, fetch_all=False)
            res = self.count_tables()
            logging.info(F"after table deletion: {res} table/s exist")
        logging.info(f'{sys._getframe().f_code.co_name} finished successfully')
        return res

    @property
    def insert_ranking_parameters(self) -> dict:
        """
        insert ref data into ranking_parameters table using data_base_client.insert_into_table api (function)
        :param table_name: the table for the data to b inserted into.
        :param json_fn: data file name
        :return: an object with success or error status
        """
        logging.info(f'{sys._getframe().f_code.co_name} started')
        output = {"status": "success", "data": f'{self.rank_tn}', "msg": ""}
        if any([self.is_delete_and_recreate_tables, self.is_truncate_tables]):
            res = self.insert_into_table(self.db_data_dir, self.rank_insert_fn, table_name=self.rank_tn)
        output['msg'] = res['status']
        logging.info(F"{sys._getframe().f_code.co_name} finished, {output['msg']}\n\n")
        return output

    @property
    def insert_products_job(self) -> dict:
        """
        insert data (products, keywords) from a file into products table using data_base_client.insert_into_table api (function)
        :param table_name: the table for the data to b inserted into - default is product table.
        :param json_dir: json folder location
        :param json_fn: json file name
        :return: an object with success or error status
        """
        logging.info(f'{sys._getframe().f_code.co_name} started')
        output = {"status": "success", "data": f'{self.products_tn}', "msg": ""}
        if any([self.is_delete_and_recreate_tables, self.is_truncate_tables]):
            res = self.insert_into_table(self.db_data_dir, self.products_insert_fn, table_name=self.products_tn)
        output['msg'] = res['status']
        logging.info(F"{sys._getframe().f_code.co_name} finished, {output['msg']}\n\n")
        return output

    def insert_new_site_into_search_engine_api(self, url: str, product: str, keywords: dict, seniority: int,
                                               ref: int = 0) -> str:
        """
        insert new website to DB
        :param url: website url
        :param seniority: age of website in days
        :param keywords: search keywords which relevant to this website
        :param ref: references to search website
        :return: website's unique url
        """
        logging.info(f'{sys._getframe().f_code.co_name} job started')
        if not all([url, product, keywords, seniority]):
            logging.info(f'{sys._getframe().f_code.co_name} existing on starting - missing all api input - no tables '
                         f'update made')
            return
        if not keywords:
            logging.info(
                f'{sys._getframe().f_code.co_name} existing when start - missing keywords api input - no tables '
                f'update made')
            return
        token = secrets.token_urlsafe()
        unique_url = F"{url}/{token}"
        query = F"insert into websites (url) values ('{url}');"
        self.exec_sql_query(query, fetch_all=False, commit=True)
        query = F"select max(id) from websites;"
        res = self.exec_sql_query(query, fetch_all=False)
        website_id = int(''.join(map(str, res.data)))
        query = F"select products.id, keywords from products where name = '{product}';"
        res = self.exec_sql_query(query, fetch_all=False)
        if res.data:
            keywords_set = set(
                value.lower() for key, value in keywords.items())  # to overcome case sensitivity differences
            product_id, keywords_selected_str, = res.data
            keywords_selected_str = keywords_selected_str.rstrip(',')
            keywords_selected_set = set(i.lower().strip() for i in keywords_selected_str.split(','))
            if keywords_set == keywords_selected_set:  # set comparison to eliminate duplicity differences
                query = F"insert into websites_products (website_id, product_id, ref, unique_url) values ({website_id}, {product_id}, {ref}, '{unique_url}');"
                self.exec_sql_query(query, fetch_all=False, commit=True)
                query = F"select max(id) from websites_products;"
                res = self.exec_sql_query(query, fetch_all=False)
                websites_products_id, = res.data
                with open(self.data_jobs_path, "a+") as tmp_rank_fn:
                    tmp_rank_fn.write(f'{websites_products_id} {seniority}\n')
        logging.info(f'{sys._getframe().f_code.co_name} job finished')
        return unique_url

    @property
    def update_ranking_job(self) -> object:
        """
        update the ranking table with the inserted websites and calculates the parameters value
        for each parameter (references, keywords and seniority)
        :return: an object with success or error status
        """
        logging.info(f'{sys._getframe().f_code.co_name} started')
        if os.path.exists(self.data_jobs_path):
            search_engine_ranking_col = "website_product_rel_id, parameter_id, parameter_value, parameter_grade"
            query = "select * from ranking_parameters;"
            res = self.exec_sql_query(query)
            for row in res.data:
                setattr(self, F"r_{row[1]}_id", row[0])  # parameter_id field
                setattr(self, F"r_{row[1]}_priority", row[2])  # parameter priority
                setattr(self, F"r_{row[1]}_grade", row[3])  # parameter_grade field
            with open(self.data_jobs_path, 'r') as rank_file:
                lines = rank_file.readlines()
                print(lines)
                for line in lines:
                    line = line.strip('\n')
                    ls_1 = line.split(' ')
                    website_products_id, seniority = ls_1
                    query = F"""insert into search_engine_ranking 
                    ({search_engine_ranking_col}) values ({website_products_id}, {self.r_seniority_id}, 
                    {self.r_seniority_grade * int(seniority)}, {self.r_seniority_grade});"""
                    res = self.exec_sql_query(query, fetch_all=False)
                    query = F"""select keywords, ref from websites_products as wp join products as p 
                                on wp.product_id = p.id where wp.id = {website_products_id};"""
                    res = self.exec_sql_query(query, fetch_all=False)
                    if res.data is None:
                        logging.info(F"cannot find website_products_id = {website_products_id} in {self.data_jobs_path}"
                                     F"it is not inserted into search_engine_ranking table")
                        continue
                    website_product_rel_id = website_products_id
                    keywords, ref = res.data
                    keywords = keywords.rstrip(',')
                    keywords_num = len(keywords.split(','))
                    query = F"""insert into search_engine_ranking ({search_engine_ranking_col})
                            values('{website_product_rel_id}','{self.r_ref_id}', {self.r_ref_grade * ref}, {self.r_ref_grade})"""
                    res = self.exec_sql_query(query)
                    query = F"""insert into search_engine_ranking ({search_engine_ranking_col})
                            values('{website_product_rel_id}','{self.r_keywords_id}', {self.r_keywords_grade * keywords_num}, {self.r_keywords_grade})"""
                    res = self.exec_sql_query(query)
        else:
            logging.info('update ranking - found no new websites to update')
            message = 'No Data Found'
        message = message if locals().get('message') else "update_ranking_job succeeded"
        logging.info(message)
        return {"status": "success", "data": [], "msg": message}

    def get_search_term_options(self, search_term, query_dir, query_fn):
        logging.info(f'{sys._getframe().f_code.co_name} started')
        query_url = read_text(query_dir, query_fn)
        # a special case of a response parsing which refers to this function only, therefore not in data_base_client
        res = self.exec_sql_query(query_url, fetch_all=True, raise_error=False)
        if res.data:
            if res.status == 'error':
                res_dict = {"status": "error", "data": F"error msg: {res.msg}\n, {res.data}",
                            "msg": "Server Unavailable"}
            else:
                res_dict = {"status": "success", "data": []}
                for idx, i in enumerate(res.data, start=1):
                    val1, val2 = i
                    res_dict['data'].append(
                        {"option_value": F"option{idx}", "product_page_url": val1, "product_unique_url": val2})
                    res_dict['msg'] = 'Data Found'
        else:
            res_dict = {"status": "success", "data": [], "msg": "No Data Found"}
        logging.info(F"{sys._getframe().f_code.co_name} finished, status: {res_dict['status']}, msg: {res_dict['msg']}")
        return res_dict

    def validate_test_result(self, res: dict, expected: dict, results_type: str) -> bool:
        """
        validatation of test results
        :param res: actual results
        :param expected: expected results
        :param results_type: type of results as specified in the cfg test input file
        :return: True if equals, False if not
        """
        exp_data = expected['results'][results_type]
        if res['data']:
            if len(res['data']) == len(exp_data):
                for idx, elem in enumerate(res['data']):
                    logging.info(F"retrieved unique url link: {elem['product_unique_url']}")
                    exp_elem = expected['results'][results_type][idx]['product_page_url']
                    if elem['product_unique_url']:
                        if not elem['product_unique_url'].startswith(
                                expected['results'][results_type][idx]['product_page_url']):
                            return False
                    elif elem['product_unique_url'] != exp_elem:
                        return False
        elif res['data'] != exp_data:
            return False
        return True

    @property
    def tear_down(self):
        logging.info(f'{sys._getframe().f_code.co_name} started')
        output = {"status": "success", "data": f'{self.data_jobs_path}', "msg": {"delete_update_rank_file": F"file deleted successfully", "db_tables": []}}
        if self.is_delete_updating_ranking_file:
            if os.path.exists(self.data_jobs_path):
                os.unlink(self.data_jobs_path)
            else:
                output['msg']['delete_update_rank_file'] = 'No file Found'
        # if in settings, the tables are set to be removed
        if self.is_delete_and_recreate_tables:
            self.delete_db_tables(self.db_data_dir, self.table_del_fn, force=False)
            self.create_db_tables(self.db_data_dir, self.table_creation_fn, force=True)
            output['msg']['db_tables'].append('tables deleted and recreated successfully')
        # by default the tables are truncated for every run - can be changed in the settings module (src.tests.settings)
        elif self.is_truncate_tables:
            deleted_tables_list = self.tables_list.split(',')
            self.truncate_tables(deleted_tables_list)
            output['msg']['db_tables'].append('tables truncated successfully')
        logging.info(F"{sys._getframe().f_code.co_name} finished, {output['msg']}\n\n")
        return output
