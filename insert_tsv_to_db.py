from typing import Dict
from collections import OrderedDict
import argparse
import csv
import glob
from io import StringIO
import re
import pymysql.cursors
from pymysql import Connection


def create_table(conn: Connection, table_name: str, column: Dict[str, str]):
    cursor = conn.cursor()
    query = "CREATE TABLE IF  NOT EXISTS {}({})".format(
        table_name,
        ', '.join([k + ' ' + v for k, v in column.items()])
    )
    print(query)
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
        ('label', 'varchar(20)'),
        ('task', 'varchar(50)'),
        ('session', 'varchar(100)'),
        ('title', 'varchar(300) NOT NULL UNIQUE'),
        ('url', 'varchar(200) NOT NULL'),
        ('introduction', 'text'),
        ('conference', 'varchar(10)'),
        ('lang', 'varchar(20)'),
        ('PRIMARY KEY', '(id)')
    ])
    check_exist_and_create_table(conn, 'papers', column_datatypes)
    cursor = conn.cursor()
    query = "CREATE TABLE IF NOT EXISTS paper_written_author(\
            author_id int(5),\
            paper_id int(4),\
            PRIMARY KEY (author_id, paper_id),\
            FOREIGN KEY (author_id)\
                REFERENCES authors (id)\
                ON DELETE CASCADE ON UPDATE CASCADE,\
            FOREIGN KEY (paper_id)\
                REFERENCES papers (id)\
                ON DELETE CASCADE ON UPDATE CASCADE\
        )".format(file_str)
    cursor.execute(query)


def insert_tsvdata(conn: Connection, data_dir: str, file_str: str, lang: str):
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
    author_rule = re.compile(r'(\(.+\))|♠')
    for fpath in files:
        year = int(fpath.replace('.tsv', '')[-4:])
        with open(fpath, 'r') as f:
            content = f.read()
            content = content.replace('\0', '')
            tsv = csv.DictReader(StringIO(content), delimiter='\t')
            rows = [row for row in tsv]
        paper_authors = [[author_rule.sub('', author).replace('\b', '')
                          for author in row['authors'].split(',')]
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
        query = "INSERT IGNORE INTO papers\
            (id, year, label, task,\
            session, title, url, introduction, conference, lang) \
            VALUES (0, {0}, %s, %s, %s, %s, %s, %s, '{1}', '{2}')\
            ".format(year, file_str.upper(), lang)
        data = [[row['class'], row['task'], row['session'],
                 row['title'], row['url'], row['introduction']]
                for row in rows]
        cursor.executemany(query, data)
        conn.commit()

        # insert information of authors writing papers
        query = "INSERT IGNORE INTO paper_written_author(author_id, paper_id)\
            SELECT authors.id, papers.id\
            from authors, papers\
            where authors.name = %s and papers.title = %s"
        for author, insert_data in zip(paper_authors, data):
            for name in author:
                cursor.execute(query, [name, insert_data[3]])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--data_dir', default='data/', type=str,
                        help='data directory. default data/')
    parser.add_argument('-s', '--str_rule', default='nlp', type=str,
                        help='file name. default `NLP`')
    parser.add_argument('-l', '--language', default='english', type=str,
                        help='language. use in insert language information. \
                        default `english`')
    args = parser.parse_args()
    conn = pymysql.connect(host='localhost',
                           user='root',
                           password='P@ssw@rd',
                           db='research_paper_db',
                           charset='utf8mb4',
                           port=33036,
                           cursorclass=pymysql.cursors.DictCursor
                           )
    insert_tsvdata(conn, args.data_dir, args.str_rule, args.language)
    conn.close()
