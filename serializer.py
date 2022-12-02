from flask import Flask
from flask_marshmallow import Marshmallow
from main import app

ma = Marshmallow(app)

# Product Schema
class ProductSchema(ma.Schema):
  class Meta:
    fields = ('id', 'name', 'description', 'price', 'qty')
