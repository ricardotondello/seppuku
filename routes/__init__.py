from flask import Blueprint
routes = Blueprint('routes', __name__)

from .gestor_dump_file import *