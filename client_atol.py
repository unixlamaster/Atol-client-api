# -*- coding: utf-8 -*-
import requests
import sys
import os
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
        self.group_code = options['group_code']

    def request_get(self, url, header_request):
#       GET      
        try:
            r = requests.get(url, headers = header_request)
        except requests.exceptions.ReadTimeout:
            print('Oops. Read timeout occured')
            raise
        except requests.exceptions.ConnectTimeout:
            print('Oops. Connection timeout occured!')
            raise
        return r.json()

    def request_post(self, url, header_request, data):
#       POST      
        try:
            r = requests.post(url, headers = header_request, data = data)
        except requests.exceptions.ReadTimeout:
            print('Oops. Read timeout occured')
            raise
        except requests.exceptions.ConnectTimeout:
            print('Oops. Connection timeout occured!')
            raise
        return r

    def getToken(self):
#       Получение токена        
        if len(self.token) == 0 or datetime.now() - self.token_timestamp > timedelta(1):
            url = '{0}/{1}?login={2}&pass={3}'.format(self.url, 'getToken', self.login, self.password)
            try:
                r = self.request_get(url, self.header_request)
                if r["error"] == "null" or r["error"] == None :
                    self.token = r["token"]
                    self.token_timestamp = datetime.strptime(r["timestamp"], "%d.%m.%Y %H:%M:%S")
                    return r["token"]
                else:
                    print (vars(r))
                    raise Exception('Возбуждено исключение').with_traceback(r)
            except requests.exceptions.HTTPError as err:
                print('Oops. HTTP Error occured')
                print('Response is: {content}'.format(content=err.response.content))
                raise
        else:
            return self.token

    def send_check(self,data):
#       Регистрация документа
        url = '{0}/{1}/{2}'.format(self.url, self.group_code, 'sell')
        header = self.header_request.copy()
        header["Token"] = self.getToken()
        try:
            print (self.request_post(url, header, data).text)
        except Exception as e:
            raise        

# Основной цикл парсера

#for line in sys.stdin:
#    ar = line.split(';')
#    if len(ar) == 12:
#        print (ar[6]," ",ar[10])


#r = requests.post('https://online.atol.ru/possystem/v4/getToken', data = {'login':'', 'pass':''})
#r = requests.post('https://testonline.atol.ru/possystem/v4/getToken', data = {'login':'', 'pass':''}, headers = {'Content-type': 'application/json; charset=utf-8'})
#r = requests.get('https://testonline.atol.ru/possystem/v4/getToken?login=login&pass=passs', headers = {'Content-type': 'application/json; charset=utf-8'})
#print (r.json())

check={
  "external_id":"17052917561851307",
  "receipt":{
    "client":{
      "email":"kkt@kkt.ru"
    },
    "company":{
      "email":"chek@romashka.ru",
      "sno":"osn",
      "inn":"5544332219",
      "payment_address":"https://v4.online.atol.ru"
    },
    "items":[
      {
        "name":"колбаса Клинский Брауншвейгская с/к в/с ",
        "price":1000.00,
        "quantity":0.3,
        "sum":300.00,
        "measurement_unit":"кг",
        "payment_method":"full_payment",
        "payment_object":"commodity",
        "vat":{
          "type":"vat18"
        }
      },
      {
        "name":"яйцо Окское куриное С0 белое",
        "price":100.00,
        "quantity":1.0,
        "sum":100.00,
        "measurement_unit":"Упаковка 10 шт.",
        "payment_method":"full_payment",
        "payment_object":"commodity",
        "vat":{
          "type":"vat10"
        }
    }
    ],
  "payments":[
    {
      "type":1,
      "sum":400.0
    }
    ],
  "vats":[
    {
      "type":"vat18",
      "sum":45.76
    },
    {
      "type":"vat10",
      "sum":9.09
    }
    ],
  "total":400.0
  },
  "service":{
    "callback_url":"http://testtest"
  },
  "timestamp":"01.02.17 13:45:00"
}
atol_client = AtolClient({'url': 'https://testonline.atol.ru/possystem/v4', 'login':os.environ['ATOLLOGIN'], 'pass': os.environ['ATOLPASS'], 'group_code': 'v4-online-atol-ru_4179'})
atol_client.send_check(check)