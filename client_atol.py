# -*- coding: utf-8 -*-
import requests
import sys
import os
import time
import re
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
        self.uuid = ""
        self.default_email = options['default_email']

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
            r = requests.post(url, headers = header_request, json = data)
        except requests.exceptions.ReadTimeout:
            print('Oops. Read timeout occured')
            raise
        except requests.exceptions.ConnectTimeout:
            print('Oops. Connection timeout occured!')
            raise
        return r.json()

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
            r = self.request_post(url, header, data)
            if r["error"] == "null" or r["error"] == None :
                print ('send_check - ok')
                print ('response:',r)
                self.uuid = r['uuid']
            else:
                print ("error, response:", r)
        except Exception as e:
            raise        

    def check_status(self):
#       Регистрация документа
        url = '{0}/{1}/{2}/{3}'.format(self.url, self.group_code, 'report', self.uuid)
        header = self.header_request.copy()
        header["Token"] = self.getToken()
        try:
            return self.request_get(url, header)
        except Exception as e:
            raise        

    def get_check_status(self):
#	loop try get check
        r={}
        for i in range(5):
            r=self.check_status()
            if r["status"] == "done":
                print (r)
                return 'fn_number:{0};fiscal_doc_num:{1};fiscal_attr:{2}'.format(r["payload"]["fn_number"],r["payload"]["fiscal_document_number"],r["payload"]["fiscal_document_attribute"])
            time.sleep(7)
        return r["error"]["text"]

    def validate_email(self, email):
        res = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", email)
        if res:
            return res.group(0)
        else:
            return self.default_email
    
    def validate_phone(self, phone):
        res = re.search(r"\+?(\d[0-9\s-]+)", phone)
        if res:
            newphone = re.sub(r'[\s\-]+', '', res.group(0), 0)
            return newphone
        else:
            return ""
        
    def check2dict(self, reestr):
        sum = float(reestr["amount"])
        check={
          "external_id":datetime.now().strftime("777%s"),
          "receipt":{
            "client":{
              "email": self.validate_email(reestr["email"]),
              "name":reestr["account_name"],
              "phone": self.validate_phone(reestr["phone"])
            },
            "company":{
              "email":"support@alltelecom.ru",
              "inn":"6161049174",
              "payment_address":"http://www.alltelecom.ru/"
            },
            "items":[
              {
                "name":'Договор {0}'.format(reestr["agrm"].agrm_id),
                "price":sum,
                "quantity":1,
                "sum":sum,
                "payment_method":"full_payment",
                "payment_object":"commodity",
              }
            ],
          "payments":[
            {
              "type":1,
              "sum":sum
            }
            ],
          "total":sum
          },
          "timestamp":'{0} {1}'.format(reestr['data_pay'],reestr['time_pay'])
        }
        return check

#atol_client = AtolClient({'url': 'https://testonline.atol.ru/possystem/v4', 
#                          'login':os.environ['ATOLLOGIN'], 'pass': os.environ['ATOLPASS'],
#                          'group_code': 'v4-online-atol-ru_4179',
#                          'default_email': 'noreply-payments@alltelecom.ru'})

#print (atol_client.validate_phone('dd +7 928 90870-25 olesy'))
#sys.exit()
# Основной цикл парсера
#for line in sys.stdin:
#    ar = line.split(';')
#    if len(ar) == 12:
#        print (ar[6]," ",ar[10])
#        print (atol_client.check2dict(ar))
#        atol_client.send_check(atol_client.check2dict(ar))
#        time.sleep(7)
#        atol_client.check_status()

#r = requests.post('https://online.atol.ru/possystem/v4/getToken', data = {'login':'', 'pass':''})
#r = requests.post('https://testonline.atol.ru/possystem/v4/getToken', data = {'login':'', 'pass':''}, headers = {'Content-type': 'application/json; charset=utf-8'})
#r = requests.get('https://testonline.atol.ru/possystem/v4/getToken?login=login&pass=passs', headers = {'Content-type': 'application/json; charset=utf-8'})
#print (r.json())




