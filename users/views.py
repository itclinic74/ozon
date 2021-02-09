from flask import render_template, request, redirect, flash, url_for, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import login_user, current_user, logout_user, login_required
from ozon import login_manager, db
from ozon.models import User, UserLogin


users = Blueprint('users', __name__)


@users.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        name = request.form.get('name')
        user = User.query.filter_by(username=name).first()
        if user:
            flash('Email address already exists')
            return redirect(url_for('users.login'))
        try:
            hash = generate_password_hash(request.form['password'])
            u = User(username=request.form['name'], email=request.form['email'], password=hash)
            db.session.add(u)
            db.session.flush()
            db.session.commit()
            return redirect(url_for('users.login'))
        except:
            db.session.rollback()
            print('Ошибка добавления в БД')
    return render_template("register.html", title='Регистрация')


@login_manager.user_loader
def load_user(user_id):
    print("load_user")
    #return User.query.filter_by(id=user_id)
    return UserLogin().fromDB(user_id, User)


@users.route('/admin')
@login_required
def admin():
    return render_template("admin.html", name=current_user.username)


@users.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form['name']).first()
        #print(user.username)
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('users.admin'))

        flash("Неверная пара логин/пароль", "error")

    return render_template("login.html", title="Авторизация")
    # if current_user.is_authenticated:
    #     return render_template('index.html')
    # form = LoginForm()
    # #print(form)
    # if form.validate_on_submit():
    #     user = User.query.filter_by(username=form.login.data).first()
    #     print("??мя юзера", user.username)
    #     if user is None or not user.check_password(form.password.data):
    #         flash('Не валидные данные')
    #         return redirect(url_for('login'))
    #     login_user(user, remember=form.remember_me.data)
    #     next_page = request.args.get('next')
    #     if not next_page or url_parse(next_page).netloc != '':
    #         next_page = url_for('index')
    #     return redirect(next_page)
    # return render_template('login.html', form=form)
    # login = request.form.get('login')
    # password = request.form.get('password')
    # print(login)
    # print(password)
    # if login and password:
    #     user = User.query.filter_by(username=login).first()
    #     print(user)
    #
    #     if check_password_hash(user.password, password):
    #         login_user(user)
    #
    #         next_page = request.args.get('next')
    #
    #         redirect(next_page)
    #     else:
    #         flash('Login or password is not correct')
    # else:
    #     flash('Please fill login and password fields')
    #
    #     return render_template('login.html')


@users.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('users.login'))


@users.route('/profile')
@login_required
def profile():
    return f"""<p><a href="{url_for('users.logout')}">Выйти из профиля</a>
                <p>user info: {current_user.get_id()}"""


@users.route('/forgot-password')
def forgot_password():
    return render_template('forgot-password.html')