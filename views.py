# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.template import Context, RequestContext
from ipaddr import IPv4Network
from ipaddr import IPv4Address
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib import messages
import ssl
# pip install requests==2.5.3
import requests

from clients.models import *
from payments.models import *
import datetime
import md5
import uuid
import MySQLdb
import json
import re
import urllib2
import urllib
import random

# Обновление 13072017, изменение реестров у СБРФ
# новый реестр - от 13072017, замена позиций аргументов и имени реестра
def load_reestr(request):
    reestr=''
    list_agr=[]
    err_numbers=[]

    reestr_id = request.FILES['reestr'].name

    for c in request.FILES['reestr'].chunks():
        reestr=reestr + c
    reestr = reestr.decode('cp1251')
    for i in reestr.split('\n'):
        if not i.startswith('=') and i!='':
            l = i.split(';')
            try:
                list_agr.append({'agrm':agreements.objects.get(number=l[5]),'amount':l[9].replace(',','.'),'id':"%s,%s" % (reestr_id,l[4])})
            except:
                err_numbers.append(l[5])
    #print list_agr

    if True:
        conn = MySQLdb.connect(host='lanbilling',user='*****',passwd='********',db='billing',charset='utf8')
        for item in list_agr:
            comment = "#%s" % (item['id'])
            cursor = conn.cursor()
            query0 = 'select count(*) from payments where comment="%s";' % comment
            cursor.execute(query0)
            if cursor.fetchone()[0] > 0:
                item['amount']=u'Платеж был проведен ранее'
            else:
                query1 = 'insert into payments (agrm_id,amount,comment,pay_date,local_date,status,mod_person,amount_cur_id,amount_cur,class_id) values (%s,%s,"%s",now(),now(),0,18,0,%s,0);' % (item['agrm'].agrm_id,item['amount'],comment,item['amount'])
                #print query1
                query2 = 'update agreements set balance=balance+%s where agrm_id=%s;' % (item['amount'],item['agrm'].agrm_id)
                #print query2
                try:
                    cursor.execute(query1)
		    #pass
                except Exception,e:
                    print e
                conn.commit()
                try:
                    cursor.execute(query2)
		    #pass
                except Exception,e:
                    print e
                conn.commit()
            cursor.close()
        conn.close()
    return render_to_response('payment_sber_report.html',locals(),context_instance=RequestContext(request))

# Add new payments algo on fiskal FZ 54 - 072017

def payment_add_sber(request):
#    print request.META
    uid = None
    v = None
    by_order_number = None
    try:
        ip = IPv4Network("%s/32" % request.META['HTTP_X_FORWARDED_FOR'].split(',')[0])
    except Exception,e:
        try:
            ip=IPv4Network("%s/32" % request.META['REMOTE_ADDR'])
        except:
            ip=IPv4Network("%s/32" % request.META['HTTP_X_REAL_IP'])
#    if ip==IPv4Network("192.168.4.136/32"):
#        v = vgroups.objects.get(vg_id=635) # test Serebraykov
#	vg_id = 635
    for s in staff.objects.all():
        if IPv4Network('%s/%s' % (s.segment,s.mask)).overlaps(ip) and s.vg_id.uid.acc_type == 2: # Если есть IP адрес и ФЛ
            v = s.vg_id
#            if v.vg_id==1:
#                v = vgroups.objects.get(vg_id=635) # test Serebraykov
            break
#    attrs = vars(v)
#    print ', '.join("%s: %s" % item for item in attrs.items())
    try:
#      print request.POST
      if 'man_new_aggr' in request.POST:
	    agrm = agreements.objects.get(number=request.POST.get('order',None))
            uid = agrm.uid
            by_order_number = request.POST.get('order',None)
      else:
        if request.POST.get('order',None):
            agrm = agreements.objects.get(number=request.POST.get('order',None))
            uid = agrm.uid
            by_order_number = request.POST.get('order',None)
        else:
            agrm = agreements.objects.get(uid=v.uid,archive=0) # Если у ФЛ 2 активных договора вернет две записи и uid не установится
            by_order_number = None
            uid = v.uid
    except:
	pass

    if by_order_number and uid.acc_type == 1: # Если ЮЛ
	title = u'Механизм оплаты недоступен'
        messages.error(request, u'По номеру договора %s данный вид оплаты недоступен.' % by_order_number)
        return render(request,'sber/get_aggr.html',locals())

    if not uid or uid.acc_type != 2: # Если у ФЛ 2 активных договора - придет сюда
	title = u'Не удалось определить номер договора'
        return render(request,'sber/get_aggr.html',locals())
# FZ 152 - не выводм полное ФИО
#    if by_order_number:
    name = uid.name.split()
    name[0]=u"%s***" % name[0][0]
    uid.name = ' '.join(name)

    title = u"Оплата услуг связи по договору %s" % agrm.number
    operator = Accounts.objects.get(uid=agrm.oper_id).name
    inn = Accounts.objects.get(uid=agrm.oper_id).inn
    agr_number = agrm.number
    balance = "%0.2f" % agrm.balance
    if balance < -50:
        amount = -1.05*balance+5
    elif balance >= -50 and balance <=0:
        amount = 105
    else:
        amount = 105
    in_sum="%0.2f" % (amount/1.05)
    amount = "%0.2f" % amount
    return render(request,'sber/payment.html',locals())


def payment_pay_sber(request):
    uid = None
    v = None
    by_order_number = None
    try:
        ip = IPv4Network("%s/32" % request.META['HTTP_X_FORWARDED_FOR'].split(',')[0])
    except Exception,e:
        try:
            ip=IPv4Network("%s/32" % request.META['REMOTE_ADDR'])
        except:
            ip=IPv4Network("%s/32" % request.META['HTTP_X_REAL_IP'])
#    if ip==IPv4Network("192.168.4.136/32"):
#        v = vgroups.objects.get(vg_id=635)
#	vg_id = 635
    for s in staff.objects.all():
        if IPv4Network('%s/%s' % (s.segment,s.mask)).overlaps(ip) and s.vg_id.uid.acc_type == 2:
            v = s.vg_id
#            if v.vg_id==1:
#                v = vgroups.objects.get(vg_id=635)
            break
    try:
#      print request.POST
      if 'man_agrm' in request.POST:
        title = u'Введите другой номер договора'
        return render(request,'sber/get_aggr_man.html',locals())
      else:
        if request.POST.get('order',None):
            agrm = agreements.objects.get(number=request.POST.get('order',None),archive=0)
            uid = agrm.uid
            by_order_number = request.POST.get('order',None)
        else:
	    agrm = agreements.objects.get(uid=v.uid)
            uid = v.uid
            by_order_number = None
    except:
        pass

    if by_order_number and uid.acc_type == 1: # Если ЮЛ
        title = u'Механизм оплаты недоступен'
        messages.error(request, u'По номеру договора %s данный вид оплаты недоступен.' % by_order_number)
        return render(request,'sber/get_aggr.html',locals())

    if (not uid or uid.acc_type != 2) or (by_order_number != request.POST.get('order')):
        title = u'Не удалось определить номер договора'
        return render(request,'sber/get_aggr.html',locals())

    # Test environment
    #login  = '*****'
    #password = '*****'
    #url_env = 'https://3dsec.sberbank.ru'
    # Real environment
    login  = 'ipcom****'
    password = '*********'
    url_env = 'https://securepayments.sberbank.ru'

    pageview='DESKTOP'
    #if re.match(ur'.*(android|ios|ipad|ipod|iphone).*',request.META['HTTP_USER_AGENT'],re.IGNORECASE):
    #    pageview='MOBILE'
    #else:
    #    pageview='DESKTOP'

    s = int(float(request.POST.get('sum',100))*100)
    p = Payment(amount=request.POST.get('sum',100),
#        agrm=uid.agreements_set.filter(archive=0)[0],
        agrm=agrm,   # берем объект по аргументу POST, а не запрос, т.к. может быть много записей
        gen_date=datetime.datetime.now(),
        uuid='n',
        payment_system='SB_fiskal')
    p.save()

    customerdetail = ''
    if request.POST.get('phone') or request.POST.get('e-mail'):
      customerdetail = "\"customerDetails\":{"
      if request.POST.get('e-mail'):
	customerdetail = customerdetail + "\"email\":\"%s\"" % request.POST.get('e-mail')
      if request.POST.get('phone') and request.POST.get('e-mail'):
	 customerdetail = customerdetail + ", "
      if request.POST.get('phone'):
	 customerdetail = customerdetail + "\"phone\":\"%s\"" % request.POST.get('phone')
      customerdetail = customerdetail +  '},'
    #print customerdetail

    dict_for_url = {
	'url_env':url_env,
        'p_sum':s,
	'p_order_num':p.id,
	'login':login,
	'password':password,
	'p_returl':urllib.quote('http://alltelecom.ru/payments/success/'),
	'p_d':u'Услуги связи по договору № %s' % p.agrm.number,
	'p_desc':p.agrm.number,
	'p_pageview':pageview,
        'p_customer_detail':customerdetail,
	'p_item_name':u'Услуги связи по договору ',
	'p_measure':u'шт.'
    }

    fiskal_url = """
%(url_env)s/payment/rest/register.do?
amount=%(p_sum)s&
currency=643&language=ru&
orderNumber=%(p_order_num)s&
userName=%(login)s&
password=%(password)s&
returnUrl=%(p_returl)s&
description=%(p_d)s&
taxSystem=1&
pageView=%(p_pageview)s&
orderBundle={
%(p_customer_detail)s
"cartItems":
{ "items":
[
{ "positionId": "1",
"name":\"%(p_item_name)s%(p_desc)s\",
"quantity":{"value":1,"measure":\"%(p_measure)s\"},
"itemAmount":%(p_sum)s,
"itemCode":"%(p_desc)s",
"tax":{"taxType":0},
"itemPrice":%(p_sum)s
}
]
}
}
        """ % dict_for_url
#    print fiskal_url
    #print(repr(fiskal_url))
    furl=re.sub("^\s+|\n|\r|\s+$", '', fiskal_url)
    r = requests.get(furl)
    #print(r.content)
    r = r.json()
    try:
       orderid=r['orderId']
       formurl=r['formUrl']
       p.uuid=orderid
       p.save()
       return HttpResponseRedirect(formurl)
    except Exception,e:
       print e
       return HttpResponse(r['errorMessage'])

def payment_success_sber(request):
    # Test environment
    #login  = '*****'
    #password = '*****'
    #url_env = 'https://3dsec.sberbank.ru'
    # Real environment
    login  = 'ipcom****'
    password = '*********'
    url_env = 'https://securepayments.sberbank.ru'

    orderid=request.GET.get('orderId')
    orderstatusurl='%s/payment/rest/getOrderStatus.do?orderId=%s&language=ru&userName=%s&password=%s' % (url_env,orderid,login,password)
    #print orderstatusurl
    r = requests.get(orderstatusurl)
    #print(r.content)
    r = r.json()

    if r['OrderStatus']==2:
# проводим платеж в биллинге
        #Изменяем статус платежа в нашей внутренней системе
        p=Payment.objects.get(id=r['OrderNumber'])
        if not p.paid:
            p.paid=True
            p.pay_date=datetime.datetime.now()
            p.save()
            comment = "SberFiskal #%s" % p.id
            conn = MySQLdb.connect(host='193.93.123.10',user='QYz1BlEuF5rJdKqO',passwd='m877JFacrNxbMnZNfmVI',db='billing',charset='utf8')
            cursor = conn.cursor()
            query1 = 'insert into payments (agrm_id,amount,comment,pay_date,local_date,status,mod_person,amount_cur_id,amount_cur,class_id) values (%s,%s,"%s",now(),now(),0,18,0,%s,0);' % (p.agrm_id,p.amount,comment,p.amount)
            #print query1
            #Добавляем платеж
            query2 = 'update agreements set balance=%s where agrm_id=%s;' % (p.agrm.balance+p.amount,p.agrm.agrm_id)
            #print query2
            try:
		#pass
                cursor.execute(query1)
            except Exception,e:
                print e
            conn.commit()
            try:
	 	#pass
                cursor.execute(query2)
            except Exception,e:
                print e
            conn.commit()
            cursor.close()
            conn.close()
            title = u'Оплата успешно завершена'
            messages.success(request, u'Платеж прошел успешно. Баланс обновится в течение нескольких минут. Спасибо, что Вы с нами.')
	    return render(request,'sber/status.html',locals())
        else:
	    title = u'Платеж был проведен ранее'
	    messages.success(request, u'Платеж был проведен ранее. Операция не завершена.')
	    return render(request,'sber/status.html',locals())
    #print r
    return HttpResponse(u'Произошла ошибка: %s' % r['ErrorMessage'])

# Получение файла выгрузки балансов для терминалов СБРФ 16032018  file_name = 183251_14032018_0001.txt

import csv

def get_list_balanses_for_sber(request):
  billing_db = MySQLdb.connect(host='193.93.123.10',user='QYz1BlEuF5rJdKqO',passwd='m877JFacrNxbMnZNfmVI',db='billing',charset='utf8')
  cursor = billing_db.cursor()
  query_state_billing = "select v.vg_id,ag.number,a.name, \
trim(',' from trim(replace(address_format(2, a.uid, '%C,%s.%S,%B,%F'), ' ,', ''))) \
from accounts as a join vgroups as v join agreements as ag on (a.uid=v.uid and ag.agrm_id=v.agrm_id) where a.type=2 and v.changed<5"
# full adress from lanbilling '%I, %r %R, %c %C, %s %S, %B, %f %F'
  date_now = datetime.datetime.strftime(datetime.datetime.now(), '%d%m%Y')
  response = HttpResponse(content_type='text/csv')
# https://stackoverflow.com/questions/10846133/django-create-csv-file-that-contains-unicode-and-can-be-opened-directly-with-exc
  response['Content-Disposition'] = 'attachment; filename = "183251_%s_0001.txt"' % date_now
#  response.write(u'\ufeff'.encode('utf8')) # BOM (optional)
  writer = csv.writer(response, delimiter=';')

  cursor.execute(query_state_billing)
  list_res_from_billing = []
  list_true_FIO = []
  list_false_FIO = []
  for i in cursor.fetchall():
    list_res_from_billing.append(i)
  cut_words = ('подъезд','этаж','(цоколь)','полуподвальное помещение',',Кв','литер','(гостевая)')
  for i in list_res_from_billing:
     # Вырезаем из адресов лишнее и удаляем пробелы
     addr = i[3].encode('utf8')
     for word in cut_words:
         if word in addr:
           #print "FIND %s in %s" % (word,addr)
           addr = addr.replace(word,'')
     addr = ''.join(addr.split())
     addr = addr.decode('utf8')
     # Ищем неверный формат ФИО
     fio = i[2]
     agrm = i[1]
     if len(fio.split()) > 3:
        list_false_FIO.append((agrm,fio,addr))
     else:
        list_true_FIO.append((agrm,fio,addr))   
  # Заполнение файла выгрузки
  for item in list_false_FIO:
    writer.writerow([ item[0].encode('1251'),item[1].encode('1251'),item[2].encode('1251'),'0.00' ])
  writer.writerow([ 'NEED','DELETE','THIS','LINE' ])
  for item in list_true_FIO:
    writer.writerow([ item[0].encode('1251'),item[1].encode('1251'),item[2].encode('1251'),'0.00' ])

  cursor.close()
  billing_db.close()
  return response

