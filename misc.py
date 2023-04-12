"""
**Misc API endpoints**
"""

import flask
from flask_cors import CORS
from flask import Blueprint, request
import util
import json
import sqlite3
import config
import regex as re

misc = Blueprint("misc",__name__)

@misc.route("/rules")
def rules():
    with open(config.rules, "r") as fp:
        return fp.read()