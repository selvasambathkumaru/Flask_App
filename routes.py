"""Modules"""
import os
import os.path
import datetime
from configparser import ConfigParser
import json
from flask import request, jsonify
from flask_sqlalchemy import SQLAlchemy
import boto3
from botocore.exceptions import NoCredentialsError
from flask_marshmallow import Marshmallow
from werkzeug.security import generate_password_hash, check_password_hash
from flask_httpauth import HTTPBasicAuth
from healthcheck import HealthCheck
from flasgger import Swagger
from flasgger.utils import swag_from
from flasgger import LazyString, LazyJSONEncoder
from models import Product
from serializer import ProductSchema
from main import app

config_object = ConfigParser()
config_object.read("config.ini")
PATH = config_object["PATH"]
local_error_log_file = PATH["Text_file_path"]
local_json_file = PATH["json_path"]
AWScrendtial = config_object["AWSCREDENTIAL"]

s3resource = boto3.client(
    "s3",
    aws_access_key_id=AWScrendtial["accesskey"],
    aws_secret_access_key=AWScrendtial["secretkey"],
)
s3resource1 = boto3.resource(
    "s3",
    aws_access_key_id=AWScrendtial["accesskey"],
    aws_secret_access_key=AWScrendtial["secretkey"],
)

db = SQLAlchemy(app)
ma = Marshmallow(app)

############ Basic Authentication ############
user_name_and_password = config_object["USERINFO"]
auth = HTTPBasicAuth()

users = {
    user_name_and_password["username"]: generate_password_hash(
        user_name_and_password["password"]
    )
}


@auth.verify_password
def verify_password(username, password):
    """Verify Username and Password"""
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None


############ Basic Authentication ############

########### SWAGGER Documentation ###########

app.config["SWAGGER"] = {"title": "Flask Swagger-UI", "uiversion": 2}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/swagger/",
}

template = dict(
    swaggerUiPrefix=LazyString(lambda: request.environ.get("HTTP_X_SCRIPT_NAME", ""))
)

app.json_encoder = LazyJSONEncoder
swagger = Swagger(app, config=swagger_config, template=template)

########### SWAGGER Documentation ###########
# pylint: disable=C0103

# Init schema
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)


def error_log(*error_message):
    """Creating Error Log File"""
    with open(local_error_log_file, "a+", encoding="utf-8") as outfile:
        outfile.write(*error_message)
        outfile.close()


# Create a Product
@app.route("/product", methods=["POST"])
@swag_from("swagger_config.yml")
@auth.login_required
def add_product():
    """Adding a product"""
    try:
        name = request.json["name"]
        description = request.json["description"]
        price = request.json["price"]
        qty = request.json["qty"]
        new_product = Product(description, name, price, qty)
        db.session.add(new_product)
        db.session.commit()
        return product_schema.jsonify(new_product)
    except Exception as exception:
        error_msg = ("Error log in POST Method", exception)
        error_log(str(error_msg))
        return exception
    return None


# Get All Products
@app.route("/product", methods=["GET"])
@swag_from("swagger_config.yml")
@auth.login_required
def get_products():
    """Get all product"""
    try:
        all_products = Product.query.all()
        result = products_schema.dump(all_products)
        return jsonify(result)
    except Exception as exception:
        error_msg = ("Error log in GET Method", exception)
        error_log(str(error_msg))
        return exception
    return None


# Get Single Products
@app.route("/product/<get_id>", methods=["GET"])
@swag_from("swagger_config.yml")
@auth.login_required
def get_single_product(get_id):
    """Get Id wise product"""
    try:
        product = Product.query.get(get_id)
        return product_schema.jsonify(product)
    except Exception as exception:
        error_msg = ("Error log in GET Method", exception)
        error_log(str(error_msg))
        return exception
    return None


# Update a Product
@app.route("/product/<update_id>", methods=["PUT"])
@swag_from("swagger_config.yml")
@auth.login_required
def update_product(update_id):
    """Update a product"""
    try:
        product = Product.query.get(update_id)
        name = request.json["name"]
        description = request.json["description"]
        price = request.json["price"]
        qty = request.json["qty"]

        product.name = name
        product.description = description
        product.price = price
        product.qty = qty
        db.session.commit()
        return product_schema.jsonify(product)

    except Exception as exception:
        error_msg = ("Error log in PUT Method", exception)
        error_log(str(error_msg))
        return exception
    return None


# Delete Product
@app.route("/product/<delete_id>", methods=["DELETE"])
@swag_from("swagger_config.yml")
@auth.login_required
def delete_product(delete_id):
    """Delete a product"""
    try:
        product = Product.query.get(delete_id)
        product.query.filter(product.id == delete_id).delete()
        db.session.commit()
        return "deleted the product successfully"
    except Exception as exception:
        error_msg = ("Error log in DELETE Method", exception)
        error_log(str(error_msg))
        return "could not delete the product"
    return None


def upload_to_aws(local_file, bucket, s3path):
    """upload a file to s3 location"""
    try:
        s3resource.upload_file(local_file, bucket, s3path)
        return True
    except FileNotFoundError:
        error_msg = "Upload to s3 - The file was not found"
        error_log(str(error_msg))
        return False
    except NoCredentialsError:
        error_msg = "Upload to s3 Bucket- Credentials not available"
        error_log(str(error_msg))
        return False
    return None


@app.route("/save_to_json", methods=["GET"])
@swag_from("swagger_config.yml")
@auth.login_required
def save_to_json_and_upload_to_s3():
    """save_to_json_and_upload_to_s3"""
    try:
        all_products = Product.query.all()
        result = products_schema.dump(all_products)

        for item in result:
            output = json.dumps(item)

            with open(local_json_file, "a+", encoding="utf-8") as file:
                file.write(output)
                file.close()

        current_time = datetime.datetime.now()
        s3_path = (
            AWScrendtial["s3path"] + "products_" + str(current_time) + "." + "json"
        )

        s3_bucket_name = AWScrendtial["s3bucketname"]
        uploaded_json = upload_to_aws(local_json_file, s3_bucket_name, s3_path)

        if uploaded_json is True:
            os.remove(local_json_file)
        else:
            error_msg = "could not delete the Json file"
            error_log(str(error_msg))
        return "Json File created and uploaded to s3 bucket successfully"
    except Exception as exception:
        error_msg = ("Error log in Saving Json", exception)
        error_log(str(error_msg))
        return exception
    return None


file_exists = os.path.exists(local_error_log_file)

current_time_now = datetime.datetime.now()
s3_path_text = (
    AWScrendtial["s3errorlogpath"] + "Error_Log_" + str(current_time_now) + ".txt"
)
bucket_name = AWScrendtial["s3bucketname"]

if file_exists is True:
    uploaded_text = upload_to_aws(local_error_log_file, bucket_name, s3_path_text)
    if uploaded_text is True:
        os.remove(local_error_log_file)
    else:
        error_msg_upload = "could not delete the Error_Log file"
        error_log(str(error_msg_upload))

health = HealthCheck()
health.add_check(add_product)
health.add_check(get_products)
health.add_check(get_single_product)
health.add_check(update_product)
health.add_check(delete_product)
health.add_check(upload_to_aws)
health.add_check(save_to_json_and_upload_to_s3)

app.add_url_rule("/healthcheck", "healthcheck", view_func=lambda: health.check())
