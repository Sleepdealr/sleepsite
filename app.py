from flask import Flask
from markupsafe import escape
from PIL import Image
import configparser
import database
import sys
import io
import os
import flask
import parser

app = Flask(__name__)
CONFIG = configparser.ConfigParser()
CONFIG.read("sleepweb.conf")


def get_template_items(title):
    return {
        "title": title,
    }


@app.route("/~")
@app.route("/")
def index():
    with open(os.path.join("static", "index.md"), "r") as f:
        return flask.render_template(
            "index.jinja",
            **get_template_items("Sleep's site :3 "),
            markdown=parser.parse_text(f.read()),
        )


@app.route("/robots.txt")
def robots():
    return flask.send_from_directory("static", "robots.txt")

@app.route("/discord")
def discord():
    return flask.render_template(
        "discord.jinja",
        **get_template_items("discord"),
        discord = CONFIG["discord"]["username"]
    )

@app.route("/img/<filename>")
def serve_image(filename):
    imdirpath = os.path.join(".", "static", "images")
    if filename in os.listdir(imdirpath):
        try:
            w = int(flask.request.args["w"])
            h = int(flask.request.args["h"])
        except (KeyError, ValueError):
            return flask.send_from_directory(imdirpath, filename)

        img = Image.open(os.path.join(imdirpath, filename))
        img.thumbnail((w, h), Image.ANTIALIAS)
        io_ = io.BytesIO()
        img.save(io_, format="JPEG")
        return flask.Response(io_.getvalue(), mimetype="image/jpeg")
    else:
        flask.abort(404)
