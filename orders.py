from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import datetime
import requests
import json
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import Required, Email

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bvhiaLbvipavb3245^&%'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'
db = SQLAlchemy(app)

#Создаем класс объекта базы данных
class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at_date = db.Column(db.String(80))
    created_at_time = db.Column(db.String(80))
    shipment_date = db.Column(db.String(80))
    order_number = db.Column(db.String(80))
    posting_number = db.Column(db.String(80))
    offer_id = db.Column(db.String(80))
    name = db.Column(db.String(80))
    quantity = db.Column(db.Integer)
    price = db.Column(db.String(80))
    status = db.Column(db.String(80))

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(30))
    password = db.Column(db.string(50))

class SignInForm(Form):
    email = StringField('Введите e-mail')
    password = PasswordField(validators=[Required()])
    submit = SubmitField('Submit')

class SignUpForm(Form):
    name = StringField('Введите имя', validators=[Required()])
    email = StringField('Введите e-mail', validators=[Required()])
    submit = SubmitField('Submit')


@app.route('/index.html')
@app.route('/')
def index():
    return render_template('index.html', title='Dashboard - MpScope Order')

@app.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    email = None
    password = None
    form = SignInForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        form.email.data = ''
        form.password.data = ''
    return render_template('sign-in.html', form=form, email=email, password=password)

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot-password.html')

@app.route('/orders', methods=['GET', 'POST'])
def ozon_request():
    #Получаем данные о заказах
    protocol = "http://"
    host = 'api-seller.ozon.ru'
    path = "/v2/posting/fbs/list"
    request_headers = {
        "Client-Id": "58959",
        "Api-Key": "320a8436-31c2-4695-b7e9-f4e8ff903d6e",
        "Content-Type": "application/json"
    }
    request_body = {
            "dir": "asc",
            "filter": {
                "since": "2020-09-01T11:40:57.126Z",
                "to": "2020-11-23T11:40:57.126Z"
            },
            "limit": 5,
            "offset": 0,
            "with": {
                "barcodes": True
            }
    }
    url = protocol + host + path
    response = requests.post(url, headers=request_headers, data=json.dumps(request_body))
    res_data = response.json()
    result = res_data['result']
    print('Тип result', type(result), result)
    for i in range(len(result)):
        #print(result[i])
        created_at = result[i]['created_at']
        shipment_date = result[i]['shipment_date']
        order_number = result[i]['order_number']
        posting_number = result[i]['posting_number']
        offer_id = result[i]['products'][0]['offer_id']
        name = result[i]['products'][0]['name']
        quantity = result[i]['products'][0]['quantity']
        price = result[i]['products'][0]['price']
        status = result[i]['status']
        #print(created_at)
        list_date_time = created_at.split('T')
        list_date = list_date_time[0].split('-')
        list_time = list_date_time[1].split(':')
        right_date = datetime.datetime(int(list_date[0]), int(list_date[1]), int(list_date[2]), int(list_time[0]), int(list_time[1]))
        date = right_date.strftime("%d.%m.%Y")
        time = right_date.strftime("%H:%M")
        print(date, time)
        print(list_date_time, list_date, list_time, right_date)
        #print(Orders.query.filter_by(posting_number=posting_number).first())
        if Orders.query.filter_by(posting_number=posting_number).first():
            try:
                Orders.query.filter_by(posting_number=posting_number).update({'quantity': quantity, 'price': price, 'status': status})
            except:
                db.session.rollback()
                print('Ошибка редактирования БД')
        else:
            try:
                p = Orders(created_at_date=date, created_at_time=time, shipment_date=shipment_date, order_number=order_number, posting_number=posting_number, offer_id=offer_id, name=name, quantity=quantity, price=price, status=status)
                db.session.add(p)
                db.session.flush()
                db.session.commit()
            except:
                db.session.rollback()
                print('Ошибка добавления в БД')
    dbdata = Orders.query.all()
    return render_template('orders.html', dbdata=dbdata)


if __name__ == '__main__':
    app.run(debug=True)