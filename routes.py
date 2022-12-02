from flask import request, jsonify
from flask_sqlalchemy import SQLAlchemy 
from flask_marshmallow import Marshmallow
from models import Product
from serializer import ProductSchema 
import os
import json
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from configparser import ConfigParser
import os.path
import boto3
from botocore.exceptions import NoCredentialsError
from configparser import ConfigParser
from healthcheck import HealthCheck
from main import app
from flask_restx import Api
health = HealthCheck()

config_object = ConfigParser()
config_object.read("config.ini")
PATH = config_object["PATH"]
local_error_log_file = PATH['Text_file_path']
local_json_file = PATH['json_path']
AWScrendtial = config_object["AWSCREDENTIAL"]

s3resource= boto3.client('s3', aws_access_key_id=AWScrendtial['accesskey'],aws_secret_access_key=AWScrendtial['secretkey'])
s3resource1 = boto3.resource('s3', aws_access_key_id=AWScrendtial['accesskey'], aws_secret_access_key=AWScrendtial['secretkey'])

db = SQLAlchemy(app)
ma = Marshmallow(app)
api = Api(app, title = 'Flask Application with Swagger Documentation', description = 'Analytics API swagger documentation', doc = '/doc')
############ Basic Authentication ############
user_name_and_password = config_object["USERINFO"]
auth = HTTPBasicAuth()

users = {
    user_name_and_password['username']: generate_password_hash(user_name_and_password['password'])
}

@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username
############ Basic Authentication ############

# Product Schema
class ProductSchema(ma.Schema):
  class Meta:
    fields = ('id', 'name', 'description', 'price', 'qty')

# Init schema
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

def error_log(*error_message):
  with open(local_error_log_file, "a+") as outfile:
        outfile.write(*error_message)
        outfile.close()

# Create a Product
@app.route('/product', methods=['POST'])
def add_product():
  try:
    name = request.json['name']
    description = request.json['description']
    price = request.json['price']
    qty = request.json['qty']
    new_product = Product(name, description, price, qty)
    db.session.add(new_product)
    db.session.commit()
    return product_schema.jsonify(new_product)
  except Exception as e:
    error_msg = ('Error log in POST Method', e) 
    error_log(str(error_msg))    

# Get All Products
@app.route('/product', methods=['GET'])
@auth.login_required
def get_products():
  try:
    all_products = Product.query.all()
    result = products_schema.dump(all_products)
    return jsonify(result)
  except Exception as e: 
    error_msg = ('Error log in GET Method', e)
    error_log(str(error_msg))   
        
# Get Single Products
@app.route('/product/<id>', methods=['GET'])
@auth.login_required
def get_product(id):
  try:
    product = Product.query.get(id)
    return product_schema.jsonify(product)
  except Exception as e: 
    error_msg = ('Error log in GET Method', e)
    error_log(error_msg)
    
# Update a Product
@app.route('/product/<id>', methods=['PUT'])
def update_product(id):
  try:
    product = Product.query.get(id)
    name = request.json['name']
    description = request.json['description']
    price = request.json['price']
    qty = request.json['qty']
    
    product.name = name
    product.description = description
    product.price = price
    product.qty = qty
    db.session.commit()
    return product_schema.jsonify(product)
  except Exception as e:
    error_msg = ('Error log in PUT Method', e) 
    error_log(error_msg)
    
# Delete Product
@app.route('/product/<id>', methods=['DELETE'])
def delete_product(id):
  try:
    product = Product.query.get(id)
    db.session.delete(product)
    db.session.commit()
    return product_schema.jsonify(product)
  except Exception as e: 
    error_msg = ('Error log in DELETE Method', e)
    error_log(error_msg)

def upload_to_aws(local_file, bucket, s3path):
  try:
    s3resource.upload_file(local_file, bucket, s3path)
    return True
  except FileNotFoundError: 
    error_msg = ('Upload to s3 - The file was not found')
    error_log(str(error_msg)) 
     
  except NoCredentialsError:
    error_msg = ('Upload to s3 Bucket- Credentials not available')
    error_log(str(error_msg))    

@app.route('/save_to_json', methods=['GET'])
@auth.login_required
def save_to_json_and_upload_to_s3():
  try:
    all_products = Product.query.all()
    result = products_schema.dump(all_products)

    for item in result:
      output = json.dumps(item)
       
      with open(local_json_file, "a+") as outfile:
        outfile.write(output)
        outfile.close()
      
    s3path= AWScrendtial['s3path']+ "sample.json"
    bucket = AWScrendtial['s3bucketname']
    uploaded = upload_to_aws(local_json_file, bucket, s3path)
    
    if uploaded == True:
      os.remove(local_json_file)
    else:
      error_msg = ('Could not delete the Json file')
      error_log(str(error_msg))
    return ("Json File created and uploaded to s3 bucket successfully")
  except Exception as e: 
    error_msg = ('Error log in Saving Json', e)
    error_log(str(error_msg))
   
file_exists = os.path.exists(local_error_log_file)
s3path= AWScrendtial['s3errorlogpath']+ "Error_Log.txt"
bucket = AWScrendtial['s3bucketname']
if file_exists == True:
  uploaded = upload_to_aws(local_error_log_file, bucket, s3path)
  if uploaded == True:
        os.remove(local_error_log_file)
  else:
    error_msg = ('Could not delete the Error_Log file')
    error_log(str(error_msg))

health.add_check(add_product)
health.add_check(get_products)
health.add_check(get_product)
health.add_check(update_product)
health.add_check(delete_product)
health.add_check(upload_to_aws)
health.add_check(save_to_json_and_upload_to_s3)

app.add_url_rule("/healthcheck", "healthcheck", view_func=lambda: health.check())