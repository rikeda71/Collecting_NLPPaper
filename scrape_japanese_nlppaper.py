from typing import List, Dict, Any
from copy import deepcopy
import argparse
import csv
import logging
from logging import getLogger, StreamHandler
import random
import re
import requests
import time
import tqdm
from bs4 import BeautifulSoup
from io import StringIO
from io import BytesIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage


logger = getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = StreamHandler()
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)

filehandler = logging.FileHandler(filename='error.log')
filehandler.setLevel(logging.WARN)
logger.addHandler(filehandler)


SESSION_CLASS_PAIR = {
    '機械翻訳': 'Machine Translation',
    '要約': 'Summarization',
    '知識獲得': 'Information Extraction',
    '情報抽出': 'Information Extraction',
    '固有表現解析': 'Information Extraction',
    '知識獲得・情報抽出': 'Information Extraction',
    '検索': 'Information Retrieval',
    '推薦システム': 'Information Retrieval',
    '評判・感情解析': 'Sentiment Analysis',
    '言語資源': 'Resources and Evaluation',
    '語彙資源・辞書': 'Resources and Evaluation',
    '語彙': 'Resources and Evaluation',
    'コーパス': 'Resources and Evaluation',
    'アノテーション': 'Resources and Evaluation',
    '埋め込み表現': 'Word-level Semantics',
    '分散表現': 'Word-level Semantics',
    '言い換え': 'Word-level Semantics',
    '言語処理応用': 'Application',
    '教育応用': 'Application',
    'Web応用': 'Application',
    '生成': 'Generation',
    '談話理解': 'Discourse',
    '談話': 'Discourse',
    '機械学習': 'Machine Learning',
    '深層学習': 'Machine Learning',
    '画像と言語': 'Machine Learning',
    '対話': 'Dialogue',
    'テキストマイニング': 'Text Mining',
    '言語分析': 'Text Mining',
    '文書分類': 'Text Mining',
    '質問応答': 'Text Mining',
    '言語学': 'Linguistics',
    '意味論': 'Linguistics',
    '意味解析': 'Linguistics',
    '含意関係': 'Linguistics',
    '形態論': 'Parsing',
    '構文解析': 'Parsing',
    '形態素・構文解析': 'Parsing'
}

CLASS_TO_SHORTNAME = {
    'Machine Translation': 'MT',
    'Information Extraction': 'IE',
    'Information Retrieval': 'IR',
    'Sentiment Analysis': 'SA',
    'Resources and Evaluation': 'RE',
    'Word-level Semantics': 'WS',
    'Machine Learning': 'ML',
}


def extract_session_titles(soup: Any) -> Dict[str, str]:
    """
    extract session titles from the proceedings page

    Args:
        soup (Any): the bs4 object of the proceedings page

    Returns:
        Dict[str, str]: {'session': 'session_title', ...}
    """

    # 論文はsession1 or 2 に書かれている
    session1 = soup.find_all(class_='session1')
    session2 = soup.find_all(class_='session2')
    session_dict = {}
    session_regexp = re.compile(r'[A-Z]\d+')
    for session in [session1, session2]:
        for s in session:
            session_name = s.find(class_='session_title')
            if session_regexp.search(session_name['id']) is None:
                continue
            if session_regexp.search(session_name.text) is None:
                continue
            session_name = session_name.text
            session_dict[session_name[:2]] = \
                re.sub(r'\(\d\)', '', session_name[3:])
    return session_dict


def extract_paper_details(trs: List[Any], page_url: str,
                          session_dict: Dict[str, str]) \
        -> List[Dict[str, Any]]:
    """
    extract details of papers
    Args:
        trs (List[Any]): the list objects of bs4 (extracted tr tag)
        page_url (str): the url of the proceedings page
        session_dict (Dict[str, str]):
         the dict of set of session number and session title

    Returns:
        List[Dict[str, Any]]: [description]
    """

    author_regexp = re.compile(r'\s\(.+?\)')
    head_regexp = re.compile(r'[○◊]')
    proceedings = []
    for tr in trs:
        tds = tr.find_all('td')
        link_tag = tr.find('a')
        link = link_tag['href'] if link_tag is not None else None
        if tds != []:
            # セッション番号: session 論文タイトル: title
            pid = tr.find('td', class_='pid')
            span = pid.find('span') if pid is not None else None
            if pid is not None and \
                    span is not None and \
                    re.search(r'[A-Z]\d+', span['id']) is not None:
                paper_info = tr.find_all('td')
                session = paper_info[0].text[:2]
                title = re.sub(r'\(.+?\)', '', paper_info[1].text)
                title_link = paper_info[1].find('a')
                # 2014 and 2015 only
                url = title_link['href'] if title_link is not None else ''
                proceedings_dict = {
                    'session': session_dict[session],
                    'title': title,
                    'url': page_url + url
                }
                # セッションとタスク名を紐づけられるものを紐づける
                if proceedings_dict['session'] in SESSION_CLASS_PAIR.keys():
                    proceedings_dict['task'] = \
                        SESSION_CLASS_PAIR[proceedings_dict['session']]
                else:
                    proceedings_dict['task'] = ''
                # タスクの短縮名も格納
                if proceedings_dict['task'] in CLASS_TO_SHORTNAME.keys():
                    proceedings_dict['class'] = \
                        CLASS_TO_SHORTNAME[proceedings_dict['task']]
                else:
                    proceedings_dict['class'] = proceedings_dict['task']
            # 2016 ~
            elif link_tag is not None and \
                    '#' not in link and \
                    'proceedings_dict' in locals():
                author_str = author_regexp.sub('', tds[1].text)
                author_str = head_regexp.sub('', author_str).replace(', ', ',')
                authors = author_str.split(',')
                proceedings_dict['url'] = page_url + link
                proceedings_dict['authors'] = authors
                proceedings.append(deepcopy(proceedings_dict))
            # 2014 ~ 2015
            elif len(tds) == 2 and \
                tds[0].text == '' and \
                    '(' in tds[1].text and \
                    'proceedings_dict' in locals():
                author_str = author_regexp.sub('', tds[1].text)
                author_str = head_regexp.sub('', author_str).replace(', ', ',')
                authors = author_str.split(',')
                proceedings_dict['authors'] = authors
                proceedings.append(deepcopy(proceedings_dict))
    return proceedings


def extract_introduction(proceedings: List[Dict[str, Any]]):
    """
    extract introductions from the proceedings papers
    Args:
        proceedings (List[Dict[str, Any]]):
         {'session': ●●●, 'title': ●●●, 'url': ●●●, 'authors': [●●●, ...], }
    """

    chaps = ['はじめに', '序論', '背景', '背景と目的', 'Introduction']

    for paper_dict in tqdm.tqdm(proceedings):
        manager = PDFResourceManager()
        laparams = LAParams()
        laparams.detect_vertical = True
        paper_pdf = requests.get(paper_dict['url'])
        instr = BytesIO()
        instr.write(paper_pdf.content)
        outstr = StringIO()
        with TextConverter(manager, outstr,
                           laparams=laparams) as device:
            interpreter = PDFPageInterpreter(manager, device)
            try:
                for page in PDFPage.get_pages(instr, set(), maxpages=1,
                                              caching=True,
                                              check_extractable=True):
                    interpreter.process_page(page)
                first = outstr.getvalue()
                intro = ''
                for chap in chaps:
                    cn = '1{}'.format(chap)
                    if cn in first:
                        top = first.find(cn) + len(cn)
                        if '．2' in first:
                            intro = first[top: first.find('．2')]
                        elif '.2' in first:
                            intro = first[top: first.find('.2')]
                        elif '。2' in first:
                            intro = first[top: first.find('。2')]
                        break
            except AttributeError:
                logger.error('error: {}'.format(paper_dict['url']))
        intro = first if intro == '' else intro
        paper_dict['introduction'] = intro
        time.sleep(1.5 + random.random())
        instr.close()
        outstr.close()


def write_tsv(proceedings: List[Dict[str, Any]], year: int):
    """
    write proceedings information to tsv file
    Args:
        proceedings (List[Dict[Any]]): [description]
        year (int): [description]
    """

    with open('data/nlp{}.tsv'.format(year), 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(['class', 'task', 'session', 'title',
                          'authors', 'url', 'introduction'])
        for paper in proceedings:
            # class: 分類先クラス, task: NLPでのタスク名,
            # session: 学会で割り振られたセッション title: 論文タイトル
            # authors: 著者らの名前, url: URL, introduction: イントロダクション
            writer.writerows([
                paper['class'],
                paper['task'],
                paper['session'],
                paper['title'],
                ','.join(paper['authors']),
                paper['url'],
                paper['introduction']
            ])


def collect_japanese_nlppaper(from_year: int, to_year: int):
    """
    collect japanese paper of natural language processing

    Args:
        from_year (int): from year of extraction range
        to_year (int): to year of extraction range
    """

    base_url = 'https://www.anlp.jp/proceedings/annual_meeting/'
    for year in range(from_year, to_year + 1):
        logger.info('scrape: {}'.format(year))
        url = '{}{}/'.format(base_url, year)
        html = requests.get(url)
        # encodingを変更しないと文字化けする
        html.encoding = html.apparent_encoding
        soup = BeautifulSoup(html.text, 'html.parser')
        logger.info('extract session titles')
        session_dict = extract_session_titles(soup)
        logger.info('extract paper details')
        proceedings = extract_paper_details(soup.find_all('tr'),
                                            url, session_dict)
        logger.info('extract introductions from proceedings papers')
        extract_introduction(proceedings)
        write_tsv(proceedings, year)
        logger.info('complete: {}'.format(year))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--from_year',
                        help='from year', default=2014, type=int)
    parser.add_argument('-t', '--to_year', help='to year',
                        default=2019, type=int)
    args = parser.parse_args()
    collect_japanese_nlppaper(args.from_year, args.to_year)
