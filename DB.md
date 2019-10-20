# DBの詳細

## research\_paper\_db

### Table

- authors
    - 著者名を格納するテーブル
    - ローマ字と日本語名を将来的に紐づけたい


| Field | Type | Null | Key | Default | Extra |
---- | ---- | ---- | ---- | ---- | ----
| id | int(5) | NO | PRI | NULL | auto\_increment |
| name | varchar(50) | NO | PRI | NULL | |


- papers
    - 論文の情報を格納するテーブル
    - 言語処理学会については，introductionを保存しているが，Abstractが存在する学会に対してはそちらを使うことを検討
    - classはtaskの略称．classを機械学習によって推測したい


| Field | Type | Null | Key | Default | Extra |
---- | ---- | ---- | ---- | ---- | ----
| id | int(4) | NO | PRI | NULL | auto\_increment |
| year | int(4) | NO | | NULL | |
| class | varchar(20) | YES | | NULL | |
| task | varchar(50) | YES | | NULL | |
| session | varchar(100) | YES | | NULL | |
| title | varchar(100) | NO | UNI | NULL | |
| url | varchar(100) | NO | | NULL | |
| introduction | varchar(100) | YES | | NULL | |
| conference   | varchar(10)  | YES  | | NULL | |
| lang         | varchar(20)  | YES  | | NULL | |


- paper\_written\_author
    - 論文と著者を結びつけるテーブル
    - 1つの論文に対して著者が複数いた場合，著者ごとにレコードを持つ．
        - 著者が3人なら，1つの論文につき，3つレコードを持つ
    - author\_idはauthorsのidを外部キーとしている
    - paper\_idはpapersのidを外部キーとしている


| Field | Type | Null | Key | Default | Extra |
---- | ---- | ---- | ---- | ---- | ----
| author\_id | int(5) | NO | PRI | NULL | |
| paper\_id | int(4) | NO | PRI | NULL | |
