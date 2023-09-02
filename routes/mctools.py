"""
**Generators/Tools API endpoints**
"""

# Do we ever plan on using this?

from flask import Blueprint

mctools = Blueprint("mctools", __name__, url_prefix="/tools")


# This is: /tools/hello/<name>
# i feel like the `input` statements would cause this to hang the api
@mctools.route("/tellraw")
def tellraw():
    # Input>>>>
    text = input("Text Input: ")

    # Text Color>>>>
    color_list = ["white", "gray", "red", "blue", "black", "green"]
    print(f"Choose Color:\n {color_list}")
    color = input("Color Input: ")

    # Text Style>>>>
    print("Choose True or False?")
    bold = input("Bold?: ").lower()
    underlined = input("Underlined?: ").lower()
    italic = input("Italic?: ").lower()
    strikethrough = input("Strikethrough?: ").lower()
    obfuscated = input("Obfuscated?: ").lower()

    # Click Events>>>>

    # events and inputs
    events = ["None", "run_command", "open_url"]
    print(f"Choose Event:\n 0.{events[0]} 1.{events[1]} 2.{events[2]}")
    event_input = int(input("Event Input: "))

    # check if user wants event
    if event_input != 0:
        value = input("result of event: ")
        clickevent = (
            "," + '"clickEvent"' + ":{" + '"action":' + f'"{events[event_input]}"'
            "," + '"value"'
            ":" + f'"{value}"'
            "}"
        )
    else:
        clickevent = ""
    # Main Command>>>
    command = (
        "/tellraw @s " + "{"
        f'"text":"{text}"{clickevent},"bold":{bold},"italic":{italic},"strikethrough":{strikethrough},"underlined":{underlined},"obfuscated":{obfuscated},"color":"{color}"'
        "}"
    )

    # Color Check>>>>
    for x in color_list:
        if color == x:
            return command
