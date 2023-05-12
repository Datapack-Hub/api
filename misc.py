"""
**Misc API endpoints**
"""

from flask import Blueprint
import config

misc = Blueprint("misc", __name__)


@misc.route("/rules")
def rules():
    with open(config.rules, "r") as fp:
        return fp.read()