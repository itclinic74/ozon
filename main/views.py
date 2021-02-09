import datetime
import json
from flask import Blueprint, current_app, session
from flask import Flask, render_template, request, redirect, flash, url_for
import requests
from ozon import Orders, db, User
from flask_login import login_user, current_user, logout_user, login_required


api = Blueprint('api', __name__)


@api.before_request
def before_request():
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))


@api.route('/index.html')
@api.route('/')
@login_required
def index():
    return render_template('index.html', title='Dashboard - MpScope Order', name=current_user.username)


@api.record
def record(state):
    db = state.app.config.get('SQLALCHEMY_DATABASE_URI')

    if db is None:
        raise Exception("This blueprint expects you to provide database access through orders.db")


@api.route('/orders', methods=['GET', 'POST'])
@login_required
def orders():
    # print('Тип result', type(resultat), resultat)
    # create_database(resultat)
    # page = request.args.get('page', 1, type=int)
    # db = current_app.config.get('SQLALCHEMY_DATABASE_URI')
    pagination = Orders.query.paginate(per_page=100)
    dbdata = pagination.items
    awaiting_packaging = Orders.query.filter_by(status='awaiting_packaging')
    awaiting_deliver = Orders.query.filter_by(status='awaiting_deliver')
    delivering = Orders.query.filter_by(status='delivering')
    delivered = Orders.query.filter_by(status='delivered')
    pagination_delivered = delivered.paginate(per_page=50)
    pagination_delivered_data = pagination_delivered.items
    cancelled = Orders.query.filter_by(status='cancelled')
    count_del = Orders.query.filter_by(status='awaiting_packaging').count()
    count_deliver = Orders.query.filter_by(status='awaiting_deliver').count()

    now = datetime.datetime.now()
    for item in awaiting_deliver:
        prev = item.time_of_wait
        print(item.name, item.status)
        #print(prev, type(prev))
        delta = now - prev
        print(delta.days)
        if delta.days > 0:
            Orders.query.filter_by(posting_number=item.posting_number).update({'status': "spor"})
            db.session.flush()
            db.session.commit()

    # Подсчет количества отправлений в статусе "Ожидают сборки"
    Dates_of_del = dict()
    last_shipment_date = 0
    for item in awaiting_packaging:
        # print(item.shipment_date, last_shipment_date)
        # str_item = str(item.shipment_date)
        if item.shipment_date != last_shipment_date:
            count_ship = Orders.query.filter(Orders.status == 'awaiting_packaging', Orders.shipment_date == item.shipment_date).count()
            Dates_of_del[item.shipment_date] = count_ship
            # print(count_ship)
        last_shipment_date = item.shipment_date
    # print(count_del)
    # for key, val in Dates_of_del.items():
    #     print(key, val)

    # Подсчет количества отправлений в статусе "Ожидают отгрузки"
    Dates_of_deliver = dict()
    last_shipment_date_deliver = 0
    for item in awaiting_deliver:
        # print(item.shipment_date, last_shipment_date)
        # str_item = str(item.shipment_date)
        if item.shipment_date != last_shipment_date_deliver:
            count_ship_deliver = Orders.query.filter(Orders.status == 'awaiting_deliver',
                                                 Orders.shipment_date == item.shipment_date).count()
            Dates_of_deliver[item.shipment_date] = count_ship_deliver
            # print(count_ship)
        last_shipment_date_deliver = item.shipment_date
    # print(count_del)
    # for key, val in Dates_of_del.items():
    #     print(key, val)
    # Кнопки "собрать" и "собрать все"
    if request.method == "POST":
        # Кнопка "Собрать" в статусе "Ожидают сборки"
        if "package" in request.form:
            posting_num = request.form['pos_num']
            #print(foo)
            posting_num = posting_num.strip()
            #print(strip_foo)
            #per = Orders.query.filter(Orders.posting_number == strip_foo).first()
            #print(per.id)
            try:
                #print(per.name)
                time_of_waiting = datetime.datetime.now()
                #print(time_of_waiting)
                Orders.query.filter_by(posting_number=posting_num).update({'status': "awaiting_deliver",
                                                                           'time_of_wait': time_of_waiting})
                db.session.flush()
                db.session.commit()
            except:
                db.session.rollback()
                print('Ошибка редактирования БД')
        # Кнопка "Собрать все" в статусе "Ожидают сборки"
        elif "package_all" in request.form:
            try:
                Orders.query.filter_by(status="awaiting_packaging").update({'status': "awaiting_deliver"})
                db.session.flush()
                db.session.commit()
            except:
                db.session.rollback()
                print('Ошибка редактирования БД')
        # Кнопка "Отправить" в статусе "Ожидают отгрузки"
        elif "deliver" in request.form:
            deliver_num = request.form['del_num']
            # print(foo)
            deliver_num = deliver_num.strip()
            # print(strip_foo)
            # per = Orders.query.filter(Orders.posting_number == strip_foo).first()
            # print(per.id)
            try:
                # print(per.name)
                Orders.query.filter_by(posting_number=deliver_num).update({'status': "delivering"})
                db.session.flush()
                db.session.commit()
            except:
                db.session.rollback()
                print('Ошибка редактирования БД')
        # Печать маркировок
        elif "marker" in request.form:
            markers = request.form.getlist("check_box")
            #print(markers)
            protocol = "http://"
            host = 'api-seller.ozon.ru'
            path = "/v2/posting/fbs/package-label"
            request_headers = {
                "Client-Id": "58959",
                "Api-Key": "df48a031-2e05-4dcd-bd2e-6cc055eb4078",
                "Content-Type": "application/json"
            }
            request_body = {
                "posting_number": markers

            }
            #print(request_body)
            url = protocol + host + path
            response = requests.request("POST", url, headers=request_headers, data=json.dumps(request_body))
            with open('/markers.pdf', mode='wb') as f:
                f.write(response.content)
        # Печать актов
        elif "act" in request.form:
            acts = request.form.getlist("check_box")
            print("acts: ", acts)
            protocol = "http://"
            host = 'api-seller.ozon.ru'
            path = "/v2/posting/fbs/act/create"
            request_headers = {
                "Client-Id": "58959",
                "Api-Key": "df48a031-2e05-4dcd-bd2e-6cc055eb4078",
                "Content-Type": "application/json"
            }
            request_body = {
                "posting_number": acts

            }
            print("request_body: ", request_body)
            url = protocol + host + path
            response = requests.request("POST", url, headers=request_headers, data=json.dumps(request_body))
            print("response: ", response)
            res_data = response.json()
            print("res_data", res_data)
            result = res_data['result']
            print("result: ", result)
            path = "/v2/posting/fbs/act/get-pdf"
            int_id = int(result['id'])
            request_body = {
                "id": int_id
            }
            print("request_body: ", request_body)
            url = protocol + host + path
            response = requests.request("POST", url, headers=request_headers, data=json.dumps(request_body))
            print("response: ", response)
            with open('/acts.pdf', mode='wb') as f:
                f.write(response.content)
    return render_template('orders.html', dbdata=dbdata, pagination=pagination, awaiting_packaging=awaiting_packaging,
                           awaiting_deliver=awaiting_deliver, delivering=delivering,
                           pagination_delivered_data=pagination_delivered_data,
                           delivered=delivered, pagination_delivered=pagination_delivered, cancelled=cancelled,
                           count_del=count_del, dates_of_del=Dates_of_del, dates_of_deliver=Dates_of_deliver, count_deliver=count_deliver,
                           name=current_user.username)


@api.route('/updatedb', methods=['GET', 'POST'])
def ozon_request():
    #db.drop_all()
    #db.create_all()
    # Получаем данные о заказах
    protocol = "http://"
    host = 'api-seller.ozon.ru'
    path = "/v2/posting/fbs/list"
    request_headers = {
        "Client-Id": "58959",
        "Api-Key": "df48a031-2e05-4dcd-bd2e-6cc055eb4078",
        "Content-Type": "application/json"
    }
    i = 0
    resultat = []
    now = datetime.datetime.now()
    now_date_time = now.isoformat() + "Z"
    # print(now_date_time)
    while i < 2500:  ## Поменять на переменную
        request_body = {
            "dir": "asc",
            "filter": {
                "since": "2020-11-01T11:40:57.126Z",
                "to": now_date_time
            },
            "limit": 50,
            "offset": i,
            "with": {
                "barcodes": True
            }
        }
        print(request_body)
        url = protocol + host + path
        response = requests.request("POST", url, headers=request_headers, data=json.dumps(request_body))
        res_data = response.json()
        result = res_data['result']
        resultat = resultat + result
        i = i + 51

    def create_database(resultat):
        for i in range(len(resultat)):
            # print(result[i])
            created_at = resultat[i]['created_at']
            shipment_date = resultat[i]['shipment_date']
            order_number = resultat[i]['order_number']
            posting_number = resultat[i]['posting_number']
            offer_id = resultat[i]['products'][0]['offer_id']
            name = resultat[i]['products'][0]['name']
            quantity = resultat[i]['products'][0]['quantity']
            price = resultat[i]['products'][0]['price']
            status = resultat[i]['status']
            # print(created_at)
            list_date_time = created_at.split('T')
            list_date = list_date_time[0].split('-')
            list_time = list_date_time[1].split(':')
            right_date = datetime.datetime(int(list_date[0]), int(list_date[1]), int(list_date[2]), int(list_time[0]),
                                           int(list_time[1]))
            date = right_date.strftime("%d.%m.%Y")
            time = right_date.strftime("%H:%M")
            ship_date_time = shipment_date.split('T')
            ship_date = ship_date_time[0].split('-')
            ship_time = ship_date_time[1].split(':')
            right_ship_date = datetime.datetime(int(ship_date[0]), int(ship_date[1]), int(ship_date[2]),
                                                int(ship_time[0]), int(ship_time[1]))
            date_of_ship = right_date.strftime("%d.%m.%Y")
            # print(date, time)
            # print(list_date_time, list_date, list_time, right_date)
            # print(Orders.query.filter_by(posting_number=posting_number).first())
            if Orders.query.filter_by(posting_number=posting_number).first():
                try:
                    Orders.query.filter_by(posting_number=posting_number).update(
                        {'quantity': quantity, 'price': price, 'status': status, 'shipment_date': date_of_ship})
                except:
                    db.session.rollback()
                    print('Ошибка редактирования БД')
            else:
                try:
                    p = Orders(created_at_date=date, created_at_time=time, shipment_date=date_of_ship,
                               order_number=order_number, posting_number=posting_number, offer_id=offer_id, name=name,
                               quantity=quantity, price=price, status=status)
                    db.session.add(p)
                    db.session.flush()
                    db.session.commit()
                except:
                    db.session.rollback()
                    print('Ошибка добавления в БД')

    create_database(resultat)

    return render_template('index.html')
