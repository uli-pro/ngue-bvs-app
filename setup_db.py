import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Flask app for database before importing
from flask import Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-for-db-setup')

from models import init_db, import_all_verses

init_db(app)

with app.app_context():
    import_all_verses()