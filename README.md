# My tools for work. 

### Getting Started
To work, install all the necessary dependencies from the file requirements.txt
```
pip install -r requirements.txt
```

## Description of tools

###  Avito API - for working with the avito API
To work, pass client_secret and client_id when initializing the class. 

You can get this information from avito.ru technical support.

Parameter `user_id` required for methods: `get_reports, get_last_report`

###### Example init avito api 
```
api_avito = AvitoAPI(avito_client_id, avito_client_secret, user_id=user_id)
```