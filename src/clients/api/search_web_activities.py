import os
import logging
import secrets
import sys
from clients.db.data_base_client import DataBaseClient

logging.getLogger()


class SearchWebsiteActivities(DataBaseClient):
    def __init__(self, db_path, data_jobs_path):
        super().__init__(db_path)
        self.data_jobs_path = data_jobs_path

    def insert_products_job(self, json_dir: str, json_fn: str, table_name: str) -> object:
        """
        insert data (products, keywords) into products table using data_base_client.insert_into_table api (function)
        :param table_name: the table for the data to b inserted into - default is product table.
        :param json_dir: json folder location
        :param json_fn: json file name
        :return: an object with success or error status
        """
        res = self.insert_into_table(json_dir, json_fn, table_name=table_name)
        logging.info(f'{sys._getframe().f_code.co_name} finished')
        return res

    def delete_db_tables(self, json_dir: str, json_fn: str,
                         force: bool = False) -> object:
        """
        deletes DB tables
        :param json_dir: json folder location
        :param json_fn: data file name
        :param force: to delete if tables exist
        :return: an object with data that contains the number of exist tables
        """
        res = self.count_tables()
        logging.info(F"number of table at starting point: {res} table/s already exist")
        if force or res.data > 0:
            self.exec_sql_queries(json_dir=json_dir, json_fn=json_fn, fetch_all=False)
            res = self.count_tables()
            logging.info(F"after table deletion: {res} table/s already exist")
        logging.info(f'{sys._getframe().f_code.co_name} finished')
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
        res = self.count_tables()
        logging.info(F"number of table at starting point: {res} table/s already exist")
        if force or res.data == 0:
            self.exec_sql_queries(json_fn=json_fn, json_dir=json_dir, fetch_all=False)
            res = self.count_tables()
            logging.info(F"after table deletion: {res} table/s already exist")
        logging.info(f'{sys._getframe().f_code.co_name} finished successfully')
        return res

    def insert_ranking_parameters(self, json_dir, json_fn, table_name) -> object:
        """
        insert ref data into ranking_parameters table using data_base_client.insert_into_table api (function)
        :param table_name: the table for the data to b inserted into.
        :param json_fn: data file name
        :return: an object with success or error status
        """
        res = self.insert_into_table(json_dir, json_fn, table_name=table_name)
        logging.info(f'{sys._getframe().f_code.co_name} finished')
        return res

    def insert_new_site_into_search_engine_api(self, url: str, product: str, keywords: dict, seniority: int,
                                               ref: int = 0) -> str:
        """
        insert new website to DB
        :param url: website url
        :param seniority: age of website in days
        :param keywords: search keywords which relevant to this website
in sea        :param ref: references to search website
        :return: website's unique url
        """
        logging.info(f'start {sys._getframe().f_code.co_name}')
        if not all([url, product, keywords, seniority]):
            logging.info(f'{sys._getframe().f_code.co_name} existing at beginning - missing api input - no tables '
                         f'update made')
            return
        if not keywords:
            logging.info(f'{sys._getframe().f_code.co_name} existing at beginning - missing api input - no tables '
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
        logging.info(f'{sys._getframe().f_code.co_name} finished')
        return unique_url

    @property
    def update_ranking_job(self) -> object:
        """
        update the ranking table with the inserted websites and calculates the parameters value
        for each parameter (references, keywords and seniority)
        :return: an object with success or error status
        """
        logging.info(f'in {sys._getframe().f_code.co_name}')
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
                    query = F"""select keywords, ref from websites_products as w join products as p 
                                on w.product_id = p.id where w.id = {website_products_id};"""
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

    def get_search_term_options(self, search_term):
        logging.info(f'in {sys._getframe().f_code.co_name}')
        query_url = F"""
                    SELECT ws.URL, wp.unique_url --, rnk.website_product_rel_id, rnk.SumVal,rnk.MaxGradeAndValue
                    FROM websites ws
                    INNER JOIN websites_products wp on ws.id=wp.website_id
                    INNER JOIN 
                        (SELECT id FROM products WHERE keywords like '%{search_term},%' )pr 
                        on wp.product_id=pr.id
                            INNER JOIN ( SELECT website_product_rel_id, sum(parameter_value)   as SumVal,
                                          max(parameter_grade*10000000+parameter_value) as MaxGradeAndValue
                            FROM search_engine_ranking
                            GROUP BY website_product_rel_id                                              
                        )rnk 
                    on wp.id=rnk.website_product_rel_id
                    ORDER BY rnk.SumVal desc,rnk.MaxGradeAndValue desc limit 3;
                    """

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

    def validate_test_result(self, res: str, expected: str) -> bool:
        """
        validatation of test results
        :param res: actual results
        :param expected: expected results
        :return: True if equals, False if not
        """
        exp_data = expected['results']['search_results']
        if res['data']:
            for idx, elem in enumerate(res['data']):
                logging.info(F"retrieved unique url link: {elem['product_unique_url']}")
                if elem['product_page_url'] == exp_data[idx]['product_page_url']:
                    if not elem['product_unique_url'].startswith(elem['product_page_url']):
                        return False
        elif res['data'] != exp_data:
            return False
        return True

    @property
    def tear_down(self):
        output = {"status": "success", "data": f'{self.data_jobs_path}', "msg": F"file deleted successfully"}
        if os.path.exists(self.data_jobs_path):
            os.unlink(self.data_jobs_path)
        else:
            output['msg'] = 'No file Found'
        logging.info(F"{sys._getframe().f_code.co_name} finished, {output['msg']}\n\n")
        return output
