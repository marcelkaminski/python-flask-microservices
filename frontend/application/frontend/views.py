# application/frontend/views.py
import requests
from . import forms
import os
from . import frontend_blueprint
from .. import login_manager
from .api.UserClient import UserClient
from .api.ProductClient import ProductClient
from .api.OrderClient import OrderClient
from flask import render_template, session, redirect, url_for, flash, request
from werkzeug.utils import secure_filename

from flask_login import current_user

@login_manager.user_loader
def load_user(user_id):
    return None


@frontend_blueprint.route('/', methods=['GET'])
def home():
    if current_user.is_authenticated:
        session['order'] = OrderClient.get_order_from_session()

    try:
        products = ProductClient.get_products()
    except requests.exceptions.ConnectionError:
        products = {
            'results': []
        }
    except :
        products = {
            'results': []
        }

    return render_template('home/index.html', products=products)


@frontend_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = forms.RegistrationForm(request.form)
    if request.method == "POST":
        if form.validate_on_submit():
            username = form.username.data

            # Search for existing user
            user = UserClient.does_exist(username)
            if user:
                # Existing user found
                flash('Please try another username', 'error')
                return render_template('register/index.html', form=form)
            else:
                # Attempt to create new user
                user = UserClient.post_user_create(form)
                if user:
                    flash('Thanks for registering, please login', 'success')
                    return redirect(url_for('frontend.login'))

        else:
            flash('Errors found', 'error')

    return render_template('register/index.html', form=form)


@frontend_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('frontend.home'))
    form = forms.LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            api_key = UserClient.post_login(form)
            if api_key:
                session['user_api_key'] = api_key
                user = UserClient.get_user()
                session['user'] = user['result']

                order = OrderClient.get_order()
                if order.get('result', False):
                    session['order'] = order['result']

                flash('Welcome back, ' + user['result']['username'], 'success')
                return redirect(url_for('frontend.home'))
            else:
                flash('Cannot login', 'error')
        else:
            flash('Errors found', 'error')
    return render_template('login/index.html', form=form)


@frontend_blueprint.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('frontend.home'))


@frontend_blueprint.route('/product/<slug>', methods=['GET', 'POST'])
def product(slug):
    response = ProductClient.get_product(slug)
    item = response['result']

    form = forms.ItemForm(product_id=item['id'])

    if request.method == "POST":
        if 'user' not in session:
            flash('Please login', 'error')
            return redirect(url_for('frontend.login'))
        order = OrderClient.post_add_to_cart(product_id=item['id'], qty=1)
        session['order'] = order['result']
        flash('Order has been updated', 'success')
    return render_template('product/index.html', product=item, form=form)


@frontend_blueprint.route('/checkout', methods=['GET'])
def summary():
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))

    if 'order' not in session:
        flash('No order found', 'error')
        return redirect(url_for('frontend.home'))
    order = OrderClient.get_order()

    if len(order['result']['items']) == 0:
        flash('No order found', 'error')
        return redirect(url_for('frontend.home'))

    OrderClient.post_checkout()

    return redirect(url_for('frontend.thank_you'))

@frontend_blueprint.route('/order/thank-you', methods=['GET'])
def thank_you():
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))

    if 'order' not in session:
        flash('No order found', 'error')
        return redirect(url_for('frontend.home'))

    session.pop('order', None)
    flash('Thank you for your order', 'success')

    return render_template('order/thankyou.html')



@frontend_blueprint.route('/admin', methods=['GET', 'POST'])
def admin():
    return render_template()

UPLOAD_FOLDER = 'application/static/images/'

@frontend_blueprint.route('/add_product', methods=['GET', 'POST'])
def add_product():
    form = forms.AddProductForm()
    if request.method == "POST":
        if form.validate_on_submit():
            print(form.image.data)
            filename = secure_filename(form.image.data.filename)
            print(UPLOAD_FOLDER + filename)
            form.image.data.save(UPLOAD_FOLDER + filename)
            api_key = ProductClient.post_product(form)
            if api_key:
                return redirect(url_for('frontend.home'))
            else:
                flash('Error', 'error')
        else:
            flash('Error', 'error')
    return render_template('admin/index.html', form=form)

@frontend_blueprint.route('/orders', methods=['GET'])
def orders():
    try:
        orders = OrderClient.get_orders()
    except requests.exceptions.ConnectionError:
        orders = {
            'results': []
        }
    return render_template('orders/index.html', orders=orders)