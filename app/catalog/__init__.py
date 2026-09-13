from flask import Blueprint

bp = Blueprint('catalog', __name__)
from . import routes
