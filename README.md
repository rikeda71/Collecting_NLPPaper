# Collecting\_NLPPaper

Collecting Research Papers of Natural Language Processing

## Target

- [x] the annual meeting of the Association for Natural Language Processing (in Japanese)
- [ ] Top conferences of Natural Language Processing
  - [ ] ACL
  - [ ] NAACL
  - [ ] EMNLP
- etc...

## Requirements

- python3
- Docker
  - docker-compose

## Usage

### install requirements library

```shell
python3 -m venv env/
source env/bin/activate
pip install -r requirements.txt
```

### collecting Japanese proceedings paper

```shell
python scrape_japanese_nlppaper.py -f `from_year` -t `to_year`
# When collecting papers have finished, fix annotations
```

### insert paper information to DB

```shell
docker-compose up -d  # wait a minute
python insert_tsv_to_db.py -d `data_dir` -s `conference name`
```


### About scripts

- scrape\_japanese\_nlppaper.py

```shell
$ python scrape_japanese_nlppaper.py --help
usage: scrape_japanese_nlppaper.py [-h] [-f FROM_YEAR] [-t TO_YEAR]

optional arguments:
  -h, --help            show this help message and exit
  -f FROM_YEAR, --from_year FROM_YEAR
                        from year
  -t TO_YEAR, --to_year TO_YEAR
                        to year
```

- insert\_tsv\_to\_db.py

```shell
$ python insert_tsv_to_db.py --help
usage: insert_tsv_to_db.py [-h] [-d DATA_DIR] [-s STR_RULE]

optional arguments:
  -h, --help            show this help message and exit
  -d DATA_DIR, --data_dir DATA_DIR
                        data directory. default data/
  -s STR_RULE, --str_rule STR_RULE
                        file name. default `nlp``
```
