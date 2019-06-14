# -*- coding: utf-8 -*-
import requests
import sys
import os
from string import Template
from datetime import timedelta
from datetime import datetime

class AtolClient(object):
    """docstring"""
 
    def __init__(self, options):
        """Constructor"""
        self.login = options['login']
        self.password = options['pass']
        self.url = options['url']
        self.token = ""
        self.token_timestamp = datetime.now() - timedelta(10)
        self.header_request = {'Content-type': 'application/json; charset=utf-8'}
    def getToken(self):
#       Получение токена        
        if len(self.token) == 0 or datetime.now() - self.token_timestamp > timedelta(1):
            url = Template('$base_url/$path?login=$login&pass=$password')
            r = requests.get(url.substitute(base_url = self.url, path = 'getToken', login=self.login, password=self.password), headers = self.header_request)
            self.token = r.json()["token"]
            self.token_timestamp = datetime.strptime(r.json()["timestamp"], "%d.%m.%Y %H:%M:%S")
            return r.json()["token"]
        else:
            return r.json()["token"]
    def send_check(self):
#       Регистрация документа
        return True

# Основной цикл парсера

#for line in sys.stdin:
#    ar = line.split(';')
#    if len(ar) == 12:
#        print (ar[6]," ",ar[10])


#r = requests.post('https://online.atol.ru/possystem/v4/getToken', data = {'login':'', 'pass':''})
#r = requests.post('https://testonline.atol.ru/possystem/v4/getToken', data = {'login':'', 'pass':''}, headers = {'Content-type': 'application/json; charset=utf-8'})
r = requests.get('https://testonline.atol.ru/possystem/v4/getToken?login=login&pass=passs', headers = {'Content-type': 'application/json; charset=utf-8'})
print (r.json())

atol_client = AtolClient({'url': 'https://testonline.atol.ru/possystem/v4', 'login':os.environ['ATOLLOGIN'], 'pass': os.environ['ATOLPASS']})