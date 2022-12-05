from configparser import ConfigParser
from flask_sqlalchemy import SQLAlchemy
from main import app

config_object = ConfigParser()
config_object.read("config.ini")
dbinfo = config_object["DATABASECREDENTIAL"]

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql://"
    + dbinfo["username"]
    + ":"
    + dbinfo["password"]
    + "@"
    + dbinfo["localhost"]
    + ":"
    + dbinfo["port"]
    + "/"
    + dbinfo["databasename"]
)
db = SQLAlchemy(app)

# pylint: disable=C0103
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.String(200))
    price = db.Column(db.Float)
    qty = db.Column(db.Integer)

    def __init__(self, description, name, price, qty):

        self.description = description
        self.name = name
        self.price = price
        self.qty = qty


with app.app_context():
    db.create_all()
