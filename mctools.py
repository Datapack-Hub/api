"""
**Generators/Tools API endpoints**
"""

import flask
from flask import Blueprint, request
import util

mctools = Blueprint("mctools",__name__,url_prefix="/tools")

# This is: /tools/hello/<name>
@mctools.route("/hello/<str:name>")
def hi(name):
    return f"Hi {name}!"