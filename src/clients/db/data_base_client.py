import json
import logging
import sqlite3
from importlib.resources import files
from typing import List
from munch import DefaultMunch

logging.getLogger()


class DataBaseClient(object):
    def __init__(self, db_name):
        self.conn = DataBaseClient._create_connection(db_name)

    @classmethod
    def _create_connection(cls, db_name) -> object:
        """ create a database connection to the SQLite database
            specified by db_file
        :param db_name: database name
        :return: a connection object
        """
        conn = None
        try:
            conn = sqlite3.connect(db_name)
        except Exception as e:
            logging.info(f'failed to create a connection to db_name: {db_name}, Error: {e}')
            raise ConnectionError(e)
        return conn

    def count_tables(self, raise_error=True) -> object:
        """
        count the number of exist tables in the DB
        :return: an object with the query result
        """
        query = "SELECT count() FROM sqlite_master WHERE type='table';"
        try:
            cur = self.conn.execute(query)
        except Exception as e:
            err_msg = {"status": "error", "data": F"query: {query}", "msg": F"{e}"}
            logging.info(err_msg)
            if raise_error:
                raise Exception(err_msg)
            return DefaultMunch.fromDict(err_msg)
        res = sum([sum(i) for i in cur.fetchall()])
        return DefaultMunch.fromDict({"status": "success", "data": res})

    def truncate_tables(self, table_list: List[str], raise_error=True) -> object:
        """
        :param raise_error: raise an error if occurs
        :param table_list: tables to be truncated
        :return: an object with the query result
        """
        for table_name in table_list:
            query = F"delete from {table_name};"
            try:
                cur = self.conn.execute(query)
            except Exception as e:
                err_msg = {"status": "error", "data": F"query: {query}", "msg": F"{e}"}
                logging.info(err_msg)
                if raise_error:
                    raise Exception(err_msg)
                return DefaultMunch.fromDict({"status": "error", "data": F"query: {query}", "msg": F"{e}"})
        res = sum([sum(i) for i in cur.fetchall()])
        return DefaultMunch.fromDict({"status": "success", "data": res})

    def exec_sql_query(self, sql_query: str, fetch_all: bool = True, raise_error=True, commit=True) -> object:
        """
        execute a single query
        :param sql_query: a string which represents a single query
        :param fetch_all: fetch a single row or all
        :param commit: whether to commit the results to the DB
        :param raise_error: stop execution when error occurs
        :return: an object with the query result
        """
        try:
            cursor = self.conn.execute(sql_query)
        except Exception as e:
            query = sql_query.replace('  ', '').replace('\n', ' ')
            err_msg = {"status": "error", "data": F"query: {query}", "msg": F"{e}"}
            logging.info(err_msg)
            if raise_error:
                raise Exception({"status": "error", "data": F"query: {query}", "msg": F"{e}"})
            return DefaultMunch.fromDict({"status": "error", "data": F"query: {query}", "msg": F"{e}"})
        if commit:
            self.conn.commit()
        res = cursor.fetchall() if fetch_all == True else cursor.fetchone()
        return DefaultMunch.fromDict({"status": "success", "data": res})

    def exec_sql_queries(self, query: List[str] = None, json_fn: str = None, json_dir: str = 'data.db_data',
                         fetch_all: bool = True, raise_error=True, commit: bool = True) -> object:
        """
        execute queries given by a list or by a json file
        :param query: a single query to get executed
        :param json_fn: json file path (path + file name)
        :param json_data: a list of queries within a json file
        :param fetch_all: fetch a single row or all
        :param raise_error: raise an error if occurs
        :param commit: whether to commit the results to the DB
        :return: an object with the query result
        """
        output = []
        if not any([json_fn, query]):
            return False
        elif json_fn:
            json_file_path = files(json_dir).joinpath(json_fn)
            data_query = DataBaseClient.load_json(json_file_path)
        elif isinstance(query, str):
            data_query = [query]
        else:
            data_query = query
        for query in data_query:
            cur = self.conn.cursor()
            try:
                cur.execute(query)
            except Exception as e:
                query = query.replace('  ', '').replace('\n', ' ')
                err_msg = {"status": "error", "data": F"query: {query}", "msg": F"{e}"}
                logging.info(err_msg)
                if raise_error:
                    raise Exception(err_msg)
                return DefaultMunch.fromDict(err_msg)
            res = cur.fetchall() if fetch_all else cur.fetchone()
            output.append(F"query: {query}  result: {res}")
            if commit:
                self.conn.commit()
        return DefaultMunch.fromDict({"status": "success", "data": output})

    def insert_into_table(self, json_fn: str, json_dir: str = 'data.db_data',
                          table_name: str = None, raise_error=True) -> object:
        """
        insert a new raw into a table (or a list of tables)
        :param table_name: a single table name for insertion
        :param json_dir: json directory for the file to be loaded from
        :param json_fn: json file to be loaded from
        :param raise_error: raise an error if occurs
        :return: an object with the query result
        """
        json_file_path = files(json_dir).joinpath(json_fn)
        content = DataBaseClient.load_json(json_file_path)
        cur = self.conn.cursor()
        for t_name in content:
            if table_name and t_name != table_name:
                continue
            table_data = content.get(t_name)
            insertion_data = table_data.get('data')
            for data_row in insertion_data:
                try:
                    cur.execute(F"INSERT INTO {t_name}({table_data.get('columns')}) VALUES ({data_row})")
                except Exception as e:
                    err_msg = {"status": "error", "data": [], "msg": F"{e}"}
                    logging.info(err_msg)
                    if raise_error:
                        raise Exception(err_msg)
                    return DefaultMunch.fromDict(err_msg)
            self.conn.commit()
        return DefaultMunch.fromDict({"status": "success", "data": cur.lastrowid})

    @classmethod
    def load_json(cls, json_path) -> dict:
        """
        open and read json file's content
        :param json_path: path of file dir + fn
        :return: a dict
        """
        with open(json_path, '+r') as file:
            content = json.load(file)
            return content
