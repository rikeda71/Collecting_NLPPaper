FROM mysql:5.7

RUN apt update && apt install -y locales \
    && rm -rf /var/lib/apt/lists/* \
    && echo "ja_JP.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen ja_JP.UTF-8

ENV LC_ALL ja_JP.UTF-8
