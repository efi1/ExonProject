import json
import logging
import sqlite3
from importlib.resources import files
from typing import List
from munch import DefaultMunch
from dataclasses import dataclass

logging.getLogger()


class DataBaseClient():
    def __init__(self, db_name):
        self.conn = DataBaseClient._create_connection(db_name)
        self.return_query_msg = ReturnQueryMsg(self.conn)

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
        res = self.return_query_msg.return_msg(query, fetch_all=False, commit=True)
        return DefaultMunch.fromDict(res)

    def truncate_tables(self, table_list: List[str], raise_error=True) -> object:
        """
        :param raise_error: raise an error if occurs
        :param table_list: tables to be truncated
        :return: an object with the query result
        """
        out = []
        for table_name in table_list:
            query = F"delete from {table_name};"
            res = self.return_query_msg.return_msg(query, commit=True)
            out.append(res)
        return DefaultMunch.fromDict({"status": "success", "data": out})

    def exec_sql_query(self, sql_query: str, fetch_all: bool = True, raise_error: bool = True, commit: bool = True) -> object:
        """
        execute a single query
        :param sql_query: a string which represents a single query
        :param fetch_all: fetch a single row or all
        :param commit: whether to commit the results to the DB
        :param raise_error: stop execution when error occurs
        :return: an object with the query result
        """
        res = self.return_query_msg.return_msg(sql_query, commit = True, fetch_all = fetch_all)
        return DefaultMunch.fromDict(res)

    def exec_sql_queries(self, query: List[str] = None, json_dir: str = None, json_fn: str = None,
                         fetch_all: bool = True, raise_error=True, commit: bool = True) -> object:
        """
        execute queries given by a list or by a json file
        :param query: a single query to get executed
        :param json_fn: json file name
        :param json_dir: json file path
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
            res = self.return_query_msg.return_msg(query)
            output.append(res)
            if commit:
                self.conn.commit()
        return DefaultMunch.fromDict({"status": "success", "data": output})

    def insert_into_table(self, json_dir: str, json_fn: str, commit: bool = True, fetch_all: bool = True,
                          table_name: str = None, raise_error: bool = True) -> object:
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
        out = []
        for t_name in content:
            if table_name and t_name != table_name:
                continue
            table_data = content.get(t_name)
            insertion_data = table_data.get('data')
            for data_row in insertion_data:
                query = F"INSERT INTO {t_name}({table_data.get('columns')}) VALUES ({data_row})"
                msg = self.return_query_msg.return_msg(query, raise_error=raise_error, commit=commit, fetch_all=fetch_all)
                out.append(msg)
        return DefaultMunch.fromDict({"status": "success", "data": out})

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


@dataclass
class ReturnQueryMsg:
    conn: object

    def parse_res(self, fetch_all):
        if fetch_all:
            res = self.cur.fetchall()
        else:
            res = self.cur.fetchone()
        if res and len(res) == 1:
            res = res[0]
        return res

    def is_error(self, query, commit, fetch_all):
        try:
            self.cur = self.conn.cursor()
            self.cur.execute(query)
            res = self.parse_res(fetch_all)
            if commit:
                self.conn.commit()
        except sqlite3.DatabaseError as err:
            return True, err
        return False, res

    def return_msg(self, query, raise_error=True, commit=True, fetch_all=True):
        msg = {"status": "", "data": "", "query": F"{query}", "msg": ""}
        is_error, res = self.is_error(query, commit, fetch_all)
        if is_error:
            msg['status'] = 'error'
            msg['msg'] = res
            logging.info(msg)
            if raise_error:
                raise Exception(msg)
        else:
            msg['status'] = 'success'
            msg['data'] = res
        return msg
