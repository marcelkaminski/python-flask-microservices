# application/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from flask import jsonify, request
from flask import Blueprint
import requests
# application/order_api/routes.py
from flask import jsonify, request, make_response
# application/models.py
from datetime import datetime


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['WTF_CSRF_ENABLED'] = False
app.config.update(
TESTING=True,
SECRET_KEY='192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf'
)
db = SQLAlchemy()
db.init_app(app)



class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    items = db.relationship('OrderItem', backref='orderItem')
    is_open = db.Column(db.Boolean, default=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def create(self, user_id):
        self.user_id = user_id
        self.is_open = True
        return self

    def to_json(self):
        items = []
        for i in self.items:
            items.append(i.to_json())

        return {
            'items': items,
            'is_open': self.is_open,
            'user_id': self.user_id
        }


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer)
    quantity = db.Column(db.Integer, default=1)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __init__(self, product_id, quantity):
        self.product_id = product_id
        self.quantity = quantity

    def to_json(self):
        return {
            'product': self.product_id,
            'quantity': self.quantity
        }
        
order_api_blueprint = Blueprint('order_api', __name__)




@order_api_blueprint.route('/api/orders', methods=['GET'])
def orders():
    items = []
    for row in Order.query.all():
        items.append(row.to_json())

    response = jsonify(items)
    return response


@order_api_blueprint.route('/api/order/add-item', methods=['POST'])
def order_add_item():
    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)

    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    user = response['result']
    p_id = int(request.form['product_id'])
    qty = int(request.form['qty'])
    u_id = int(user['id'])

    known_order = Order.query.filter_by(user_id=u_id, is_open=1).first()

    if known_order is None:
        known_order = Order()
        known_order.is_open = True
        known_order.user_id = u_id

        order_item = OrderItem(p_id, qty)
        known_order.items.append(order_item)
    else:
        found = False

        for item in known_order.items:
            if item.product_id == p_id:
                found = True
                item.quantity += qty

        if found is False:
            order_item = OrderItem(p_id, qty)
            known_order.items.append(order_item)

    db.session.add(known_order)
    db.session.commit()
    response = jsonify({'result': known_order.to_json()})
    return response


@order_api_blueprint.route('/api/order', methods=['GET'])
def order():
    api_key = request.headers.get('Authorization')

    response = UserClient.get_user(api_key)

    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    user = response['result']
    open_order = Order.query.filter_by(user_id=user['id'], is_open=1).first()

    if open_order is None:
        response = jsonify({'message': 'No order found'})
    else:
        response = jsonify({'result': open_order.to_json()})
    return response


@order_api_blueprint.route('/api/order/checkout', methods=['POST'])
def checkout():
    api_key = request.headers.get('Authorization')

    response = UserClient.get_user(api_key)

    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    user = response['result']

    order_model = Order.query.filter_by(user_id=user['id'], is_open=1).first()
    order_model.is_open = 0

    db.session.add(order_model)
    db.session.commit()

    response = jsonify({'result': order_model.to_json()})
    return response




class UserClient:
    @staticmethod
    def get_user(api_key):
        headers = {
            'Authorization': api_key
        }
        response = requests.request(method="GET", url='http://192.168.0.106:5001/api/user', headers=headers)
        if response.status_code == 401:
            return False
        user = response.json()
        return user


with app.app_context():
    app.register_blueprint(order_api_blueprint)

migrate = Migrate(app, db)


if __name__ == '__main__':
    
    app.run(host='0.0.0.0', port=5003)
