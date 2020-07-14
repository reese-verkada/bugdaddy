from flask import Flask
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import flask_saml
from .config import *
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
cors = CORS(app, supports_credentials=True)
app.config.update({
	'SECRET_KEY': SAML_SECRET_KEY,
	'SAML_METADATA_URL': SAML_METADATA_URL,
	'SAML_DEFAULT_REDIRECT': '/api/redirect?to='+FRONTEND_URL,
	'PERMANENT_SESSION_LIFETIME': timedelta(minutes=SESSION_TIMEOUT),
	'SQLALCHEMY_DATABASE_URI': DATABASE_URI,
	'SQLALCHEMY_TRACK_MODIFICATIONS': False
})
flask_saml.FlaskSAML(app)
db = SQLAlchemy(app)

from . import main