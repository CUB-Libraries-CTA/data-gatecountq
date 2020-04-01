data-gatecountq Queue
======================

This celery queue has tasks that will pull Gate Count from Vea SenSource API.

Requirements
------------

1. Cybercom API with mongodb 
2. Vea SenSource API account (token)


Dependencies
------------

Environment Variables (Required):

* SENSOURCE_ID = Vea SenSource Client ID 
* SENSOURCE_SECRET =  Vea SenSource Client Secret 
* CYBERCOM_TOKEN = Cybercom token that allows edit within collection

Environment Variables (Optional)

* CYBERCOM_COLLECTION =  MongoDB Collection to store gate count (default: gatecount)


Author Information
------------------

[Mark Stacy](https://github.com/mbstacy)