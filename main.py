from flask import Flask
import os

# Init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

def create_app():
  with app.app_context():
    import routes
    import models
    import serializer
    
  return app