from typing import Dict
from collections import OrderedDict
import argparse
import csv
import glob
from io import StringIO
import pymysql.cursors
from pymysql import Connection


def create_table(conn: Connection, table_name: str, column: Dict[str, str]):
    cursor = conn.cursor()
    query = "CREATE TABLE {}({})".format(
        table_name,
        ', '.join([k + ' ' + v for k, v in column.items()])
    )
    cursor.execute(query)


def check_exist_and_create_table(conn: Connection, table_name: str,
                                 column: Dict[str, str]) -> bool:
    query = "show tables like '{}'".format(table_name)
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    if not result:
        create_table(conn, table_name, column)
        return True
    return False


def prepare_table(file_str: str):
    column_datatypes = OrderedDict([
        ('id', 'int(4) NOT NULL AUTO_INCREMENT'),
        ('year', 'int(4) NOT NULL'),
        ('class', 'varchar(20)'),
        ('task', 'varchar(50)'),
        ('session', 'varchar(100)'),
        ('title', 'varchar(300) NOT NULL UNIQUE'),
        ('url', 'varchar(200) NOT NULL'),
        ('introduction', 'text'),
        ('PRIMARY KEY', '(id)')
    ])
    if check_exist_and_create_table(conn, '{}_papers'.format(file_str),
                                    column_datatypes):
        cursor = conn.cursor()
        query = "CREATE TABLE {0}_paper_written_author(\
                author_id int(5),\
                paper_id int(4),\
                PRIMARY KEY (author_id, paper_id),\
                FOREIGN KEY (author_id)\
                    REFERENCES authors (id)\
                    ON DELETE RESTRICT ON UPDATE RESTRICT,\
                FOREIGN KEY (paper_id)\
                    REFERENCES {0}_papers (id)\
                    ON DELETE RESTRICT ON UPDATE RESTRICT\
            )".format(file_str)
        cursor.execute(query)


def insert_tsvdata(conn: Connection, data_dir: str, file_str: str):
    # check authors table exist
    check_exist_and_create_table(conn, 'authors',
                                 OrderedDict([
                                     ('id', 'int(5) NOT NULL AUTO_INCREMENT'),
                                     ('name', 'varchar(50) NOT NULL UNIQUE'),
                                     ('PRIMARY KEY', '(id, name)')
                                 ]))
    data_dir = data_dir + '/' if data_dir[-1] != '/' else data_dir
    files = glob.glob('{}{}*'.format(data_dir, file_str))
    prepare_table(file_str)
    for fpath in files:
        print(fpath)
        year = int(fpath.replace('.tsv', '')[-4:])
        with open(fpath, 'r') as f:
            content = f.read()
            content = content.replace('\0', '')
            tsv = csv.DictReader(StringIO(content), delimiter='\t')
            rows = [row for row in tsv]
        paper_authors = [[author for author
                          in row['authors'].split(',')]
                         for row in rows]
        # insert author names
        authors = list(set(
            [author for paper_author in paper_authors
             for author in paper_author]
        ))
        query = "INSERT IGNORE INTO authors VALUES(0, %s)"
        cursor = conn.cursor()
        cursor.executemany(query, authors)
        conn.commit()

        # insert paper informations
        query = "INSERT IGNORE INTO {0}_papers\
            (id, year, class, task,\
            session, title, url, introduction) \
            VALUES (0, {1}, %s, %s, %s, %s, %s, %s)".format(file_str, year)
        data = [[row['class'], row['task'], row['session'],
                 row['title'], row['url'], row['introduction']]
                for row in rows]
        print(len(data))
        cursor.executemany(query, data)
        conn.commit()

        # insert information of authors writing papers
        query = "INSERT IGNORE INTO {0}_paper_written_author(author_id, paper_id)\
            SELECT authors.id, {0}_papers.id\
            from authors, {0}_papers\
            where authors.name = %s and {0}_papers.title = %s\
        ".format(file_str)
        for author, insert_data in zip(paper_authors, data):
            for name in author:
                cursor.execute(query, [name, insert_data[3]])
                print(insert_data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--data_dir', default='data/', type=str,
                        help='data directory. default data/')
    parser.add_argument('-s', '--str_rule', default='nlp', type=str,
                        help='file name. default `nlp``')
    args = parser.parse_args()
    conn = pymysql.connect(host='localhost',
                           user='root',
                           password='P@ssw@rd',
                           db='research_paper_db',
                           charset='utf8mb4',
                           port=3306,
                           cursorclass=pymysql.cursors.DictCursor
                           )
    insert_tsvdata(conn, args.data_dir, args.str_rule)
    conn.close()
