
import requests
import sys


# Основной цикл парсера

#for line in sys.stdin:
#    ar = line.split(';')
#    if len(ar) == 12:
#        print (ar[6]," ",ar[10])


#r = requests.post('https://online.atol.ru/possystem/v4/getToken', data = {'login':'', 'pass':''})
#r = requests.post('https://testonline.atol.ru/possystem/v4/getToken', data = {'login':'', 'pass':''}, headers = {'Content-type': 'application/json; charset=utf-8'})
r = requests.get('https://testonline.atol.ru/possystem/v4/getToken?login=login&pass=passs', headers = {'Content-type': 'application/json; charset=utf-8'})
print (r.json())