<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [My tools for work](#my-tools-for-work)
  - [Getting Started](#getting-started)
- [Description](#description)
  - [Common](#common)
    - [avito_api.py](#avito_apipy)
      - [Examples](#examples)
  - [tg_event_messeger.py - functions fro working with request methods](#tg_event_messegerpy---functions-fro-working-with-request-methods)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


# My tools for work
Description

## Getting Started
To work, install all the necessary dependencies from the file requirements.txt
```
pip install -r requirements.txt
```

# Description

## Common
This folder contains common tools
### avito_api.py

For working with the avito API.

To work, pass client_secret and client_id when initializing the class. 

You can get this information from avito.ru technical support.

Parameter `user_id` required for methods: `get_reports, get_last_report`

#### Examples
- Init AvitoAPI:

    ```
    api_avito = AvitoAPI(avito_client_id, avito_client_secret, user_id=user_id)
    ```
- Get last report

    ```
    api_avito = AvitoAPI(avito_client_id, avito_client_secret, user_id=user_id)
    ```

##  tg_event_messeger.py - functions fro working with request methods