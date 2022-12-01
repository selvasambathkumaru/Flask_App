from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy 
from flask_marshmallow import Marshmallow 
import os
import json
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import os.path
import boto3
from botocore.exceptions import NoCredentialsError
from configparser import ConfigParser

config_object = ConfigParser()
config_object.read("config.ini")
dbinfo = config_object["DATABASECREDENTIAL"]
local_error_log_file = "D:\\Python_Topics\\Flask\\POC\\API_Health_Check\\Error_Log.txt"

# Init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# Database
app.config['SQLALCHEMY_DATABASE_URI']='mysql://'+ dbinfo["username"]+":" + dbinfo["password"]+"@"+dbinfo["localhost"]+":"+dbinfo["port"]+'/'+dbinfo["databasename"]
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)

############ Basic Authentication ############
auth = HTTPBasicAuth()

users = {
    "Selva": generate_password_hash("Sambath")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username
############ Basic Authentication ############

# Product Class/Model
class Product(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), unique=True)
  description = db.Column(db.String(200))
  price = db.Column(db.Float)
  qty = db.Column(db.Integer)

  def __init__(self, name, description, price, qty):
    self.name = name
    self.description = description
    self.price = price
    self.qty = qty

with app.app_context():
    db.create_all()
    
# Product Schema
class ProductSchema(ma.Schema):
  class Meta:
    fields = ('id', 'name', 'description', 'price', 'qty')

# Init schema
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

def error_log(error_message):
  with open(local_error_log_file, "a+") as outfile:
        outfile.write(error_message)
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
    error_log(error_msg)     

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
    error_log(error_msg)    
        
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

AWScrendtial = config_object["AWSCREDENTIAL"]

s3resource= boto3.client('s3', aws_access_key_id=AWScrendtial['accesskey'],aws_secret_access_key=AWScrendtial['secretkey'])
s3resource1 = boto3.resource('s3', aws_access_key_id=AWScrendtial['accesskey'], aws_secret_access_key=AWScrendtial['secretkey'])

def upload_to_aws(local_file, bucket, s3path):
  try:
    s3resource.upload_file(local_file, bucket, s3path)
    return "True"
  except FileNotFoundError: 
    error_msg = ('Upload to s3 - The file was not found')
    error_log(error_msg)  
     
  except NoCredentialsError:
    error_msg = ('Upload to s3 Bucket- Credentials not available')
    error_log(error_msg)     

@app.route('/save_to_json', methods=['GET'])
@auth.login_required
def save_to_json_and_upload_to_s3():
  try:
    all_products = Product.query.all()
    result = products_schema.dump(all_products)

    local_json_file = "D:\\Python_Topics\\Flask\\POC\\API_Health_Check\\sample.json" 
    for item in result:
      output = json.dumps(item)
       
      with open(local_json_file, "a+") as outfile:
        outfile.write(output)
        outfile.close()
      
    s3path= AWScrendtial['s3path']+ "sample.json"
    bucket = AWScrendtial['s3bucketname']
    uploaded = upload_to_aws(local_json_file, bucket, s3path)
    
    if uploaded == 'True':
      os.remove(local_json_file)
    else:
      error_msg = ('Could not delete the Json file')
      error_log(error_msg) 
    return ("Json File created and uploaded to s3 bucket successfully")
  except Exception as e: 
    error_msg = ('Error log in Saving Json', e)
    error_log(error_msg) 
   
file_exists = os.path.exists(local_error_log_file)
s3path= AWScrendtial['s3errorlogpath']+ "Error_Log.txt"
bucket = AWScrendtial['s3bucketname']
if file_exists == True:
  uploaded = upload_to_aws(local_error_log_file, bucket, s3path)
  if uploaded == 'True':
        os.remove(local_error_log_file)
  else:
    error_msg = ('Could not delete the Error_Log file')
    error_log(error_msg) 

# Run Server
if __name__ == '__main__':
  app.run(debug=True)
