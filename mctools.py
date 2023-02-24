"""
**Generators/Tools API endpoints**
"""

import flask
from flask import Blueprint, request
import util

mctools = Blueprint("mctools",__name__,url_prefix="/tools")

# This is: /tools/hello/<name>
@mctools.route("/tellraw")
def tellraw():
    #Input
    text = input("Text Input: ")

    #Text Color
    color_list = ['red','blue','black','green']
    print(f"Choose Color:\n {color_list}")
    color = input("Color Input: ")

    #Text Style
    print("Choose True or False?")
    bold = input("Bold?: ").lower()
    strikethrough = input("Strikethrough?: ").lower()
    underlined = input("Underlined?: ").lower()
    obfuscated = input("Obfuscated?: ").lower()

    #Main Command
    command = f"/tellraw @s " + '{'f'"text":"{text}","bold":{bold},"strikethrough":{strikethrough},"underlined":{underlined},"obfuscated":{obfuscated},"color":"{color}"''}'

    #Color Check
    for x in color_list:
     if color == x:
      print(command)

    return command   
 