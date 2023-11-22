import os
import logging
import re
import secrets
from munch import DefaultMunch
from importlib.resources import files
from src.clients.db.data_base_client import DataBaseClient

DATA_PTAH = files('data.cfg_tests')
DATA_TEMP_FILE = files('data.jobs_data').joinpath('to_be_inserted_into_ranking.txt')
logging.getLogger()


class SearchWebsiteActivities(DataBaseClient):
    def __init__(self, db_name):
        super().__init__(db_name)

    def delete_db_tables(self, json_fn: str = 'tables_deletion.json', force: bool = False) -> object:
        """
        deletes DB tables
        :param force: to delete if tables exist
        :return: an object with data that contains the number of exist tables
        """
        res = inst.count_tables()
        logging.info(F"number of table at starting point: {res} table/s already exist")
        if force or res.data > 1:
            inst.exec_sql_queries(json_fn=json_fn, fetch_all=False)
            res = inst.count_tables()
            logging.info(F"after table deletion: {res} table/s already exist")
        return res

    def create_db_tables(self, json_fn: str = 'tables_creation.json', json_dir='data.db_data',
                         force: bool = False) -> object:
        """
        create DB tables
        :param json_fn:
        :param force: to create also if already exist
        :return: an object with data that contains the number of created tables
        """
        res = inst.count_tables()
        logging.info(F"number of table at starting point: {res} table/s already exist")
        if force or res.data == 1:
            inst.exec_sql_queries(json_fn=json_fn, json_dir=json_dir, fetch_all=False)
            res = inst.count_tables()
            logging.info(F"after table deletion: {res} table/s already exist")
        return res

    def insert_products_job(self, table_name='products', json_fn='db_data_insertion.json',
                            json_dir='data.db_data') -> object:
        """
        insert data (products, keywords) into products table using data_base_client.insert_into_table api (function)
        :param table_name: the table for the data to b inserted into - default is product table.
        :return: an object with success or error status
        """
        res = inst.insert_into_table(json_fn, json_dir=json_dir, table_name=table_name)
        return res

    def insert_ranking_parameters(self, table_name='ranking_parameters', json_fn='db_data_insertion.json',
                            json_dir='data.db_data') -> object:
        """
        insert ref data into ranking_parameters table using data_base_client.insert_into_table api (function)
        :param table_name: the table for the data to b inserted into.
        :return: an object with success or error status
        """
        res = inst.insert_into_table(json_fn, json_dir=json_dir, table_name=table_name)
        return res

    def insert_new_site_into_search_engine_api(self, url: str, product: str, keywords: dict, seniority: int,
                                               ref: int = 0) -> str:
        """
        insert new website to DB
        :param url: website url
        :param seniority: age of website in days
        :param keywords: search keywords which relevant to this website
        :param ref: references to serach website
        :return: website's unique url
        """
        unique_url = F"{url}token={secrets.token_urlsafe()}"
        query = F"insert into websites (url) values ('{url}');"
        self.exec_sql_query(query, fetch_all=False, commit=True)
        query = F"select max(id) from websites;"
        res = self.exec_sql_query(query, fetch_all=False)
        website_id = int(''.join(map(str, res.data)))
        query = F"select products.id, keywords from products where name = '{product}';"
        res =  self.exec_sql_query(query, fetch_all=False)
        if res.data:
            keywords_set = set(value.lower() for key, value in keywords.items()) #to overcome case sensitivity differences
            product_id, keywords_selected_str,  = res.data
            keywords_selected_str = keywords_selected_str.rstrip(',')
            keywords_selected_set = set(i.lower().strip() for i in keywords_selected_str.split(','))
            if keywords_set == keywords_selected_set: # set comparison to eliminate duplicity differences
                query = F"insert into websites_products (website_id, product_id, ref, unique_url) values ({website_id}, {product_id}, {ref}, '{unique_url}');"
                self.exec_sql_query(query, fetch_all=False, commit=True)
                query = F"select max(id) from websites_products;"
                res = self.exec_sql_query(query, fetch_all=False)
                websites_products_id, = res.data
                with open(DATA_TEMP_FILE, "a+") as tmp_rank_fn:
                    tmp_rank_fn.write(f'{websites_products_id} {seniority}\n')
        return unique_url

    def update_ranking_job(self) -> object:
        """
        update the ranking table with the inserted websites and calculates the parameters value
        for each parameter (references, keywords and seniority)
        :return: an object with success or error status
        """
        search_engine_ranking_col = "website_product_rel_id, parameter_id, parameter_value, parameter_grade"
        query = "select * from ranking_parameters;"
        res = self.exec_sql_query(query)
        for row in res.data:
            setattr(self, F"r_{row[1]}_id", row[0]) # parameter_id field
            setattr(self, F"r_{row[1]}_priority", row[2]) # parameter priority
            setattr(self, F"r_{row[1]}_grade", row[3]) # parameter_grade field
        if os.path.exists(DATA_TEMP_FILE):
            with open(DATA_TEMP_FILE, 'r') as rank_file:
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
                        logging.info(F"cannot find website_products_id = {website_products_id} in {DATA_TEMP_FILE}"
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
            os.unlink(DATA_TEMP_FILE)  # delete the jobs_data file with seniority data
        else:
            logging.info('update ranking - found no new websites to update')
            message = "update ranking - found no new websites to update"
        message = message if locals().get('message') else "update_ranking_job succeeded"
        logging.info(message)
        return DefaultMunch.fromDict({"status": "success", "data": [], "msg": message})


    def get_search_term_options(self, search_term):
        query_url = F"""
                    SELECT ws.URL --, rnk.website_product_rel_id, rnk.SumVal,rnk.MaxGradeAndValue
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
                res_dict = {"status": "error", "data": F"error msg: {res.msg}\n, {res.data}", "msg": "Server Unavailable"}
            else:
                res_dict = {"status" : "success", "data": []}
                for idx, i in enumerate(res.data, start=1):
                    val, = i
                    res_dict['data'].append({"option_value": F"option{idx}", "product_page_url": val})
        else:
            res_dict = {"status": "success", "data": [], "msg": "No Data Found"}
        return res_dict



if __name__ == '__main__':
    db_name = '../db/search_engine.db'
    inst = SearchWebsiteActivities(db_name)

    # truncate tables
    inst.truncate_tables(['websites', 'websites_products', 'search_engine_ranking'])

    # delete temp data file if exist
    # if os.path.exists(DATA_TEMP_FILE):
    #     os.unlink(DATA_TEMP_FILE)

    # delete tables
    # inst.delete_db_tables()
    # inst.create_db_tables()

    # inser reference data into ranking_parameters table
    inst.insert_ranking_parameters()

    # run insert product job
    inst.insert_products_job()

    # insert_new_site_into_search_engine_api
    websites_insertion_d = DataBaseClient.load_json(DATA_PTAH.joinpath('test_1.json'))
    for website in websites_insertion_d['websites']:
        res = inst.insert_new_site_into_search_engine_api(website['url'], website['product'], website['keywords'], website['seniority'], website['ref'])

    # run update_ranking_job process
    res = inst.update_ranking_job()

    # delete data file when update_ranking_job finishes
    if os.path.exists(DATA_TEMP_FILE):
        os.unlink(DATA_TEMP_FILE)

    # search term
    res = inst.get_search_term_options('leisure time')
    assert res['status'] == 'success', F"Error occurred {res['data']}"
    print(res)

    # view the content of DB files
    query = [f'select * from websites_products order by website_id;', f'select * from websites order by id;', f'select * from search_engine_ranking order by website_product_rel_id;']
    # res = inst.exec_sql_queries(query, fetch_all=True)
    # res = ''.join(res.data)
    # pattern = r"[;|)|]"
    # result = re.split(pattern, res)
    # for i in result:
    #     print(f'{i}')

