<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
# Table of Contents

- [My tools for work](#my-tools-for-work)
  - [Getting Started](#getting-started)
- [common/](#common)
  - [avito_api.py](#avito_apipy)
    - [Examples](#examples)
  - [tg_event_messeger.py](#tg_event_messegerpy)
    - [Examples](#examples-1)
  - [ya_bucket.py](#ya_bucketpy)
    - [Examples](#examples-2)
- [flask/](#flask)
  - [common/](#common-1)
    - [auth.py](#authpy)
    - [decorators.py](#decoratorspy)
    - [test_case.py](#test_casepy)
  - [mongo/](#mongo)
    - [utils.py](#utilspy)
  - [sql/](#sql)
    - [marshmallow.py](#marshmallowpy)
    - [utils.py](#utilspy-1)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


# My tools for work
Description

## Getting Started
To work, install all the necessary dependencies from the file requirements.txt
```
pip install -r requirements.txt
```

# common/
This folder contains common tools
## avito_api.py

For working with the avito API.

To work, pass client_secret and client_id when initializing the class. 

You can get this information from avito.ru technical support.

Parameter `user_id` required for methods: `get_reports, get_last_report`

### Examples
- Init AvitoAPI:

    ```
    api_avito = AvitoAPI(avito_client_id, avito_client_secret, user_id=user_id)
    ```
- Get last report

    ```
    api_avito = AvitoAPI(avito_client_id, avito_client_secret, user_id=user_id)
    ```

##  tg_event_messeger.py 
Sending event messages in a Telegram

### Examples
- Init:

##  ya_bucket.py
Методы для работы c YandexBucket. Используется библиотека boto3

### Examples
- Init YandexBucket:

# flask/
Here are my tools for convenient work with Flask

## common/
General helper scripts.
Do not import, only copy to the project and edit

### auth.py
Methods for authorization and authentication
### decorators.py
Decorators
### test_case.py
General test case

## mongo/
For using MongoDB and mongoengine
### utils.py

## sql/
Tools for working with Flask + SQL
### marshmallow.py
Auxiliary functions for working with marshmallow
### utils.py
Auxiliary functions for working with data received from the database




