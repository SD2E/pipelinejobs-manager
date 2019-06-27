import json
import os
import pytest
import yaml
from attrdict import AttrDict

@pytest.fixture(scope='session')
def mongodb_settings():
    settings = {'host': 'localhost', 'port': 27017,
                'username': 'catalog', 'password': 'catalog',
                'database': 'catalog_local',
                'auth_source': 'catalog_local'}
    return settings

# base64.urlsafe_b64encode('<connectionString>'.encode('utf-8')).decode('utf-8')
@pytest.fixture(scope='session')
def mongodb_authn():
    authn = 'bW9uZ29kYjovL2NhdGFsb2c6Y2F0YWxvZ0Bsb2NhbGhvc3Q6MjcwMTcvY2F0YWxvZ19sb2NhbD9yZWFkUHJlZmVyZW5jZT1wcmltYXJ5'
    return {'authn': authn, 'database': 'catalog_local'}
