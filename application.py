from flask import Flask, redirect, request
from paste.translogger import TransLogger
from waitress import serve
from PIL import Image
import configparser
import database
import sys
import io
import os
import flask
import parser
import database
import random

app = Flask(__name__)
CONFIG = configparser.ConfigParser()
CONFIG.read("sleepweb.conf")
shown_images = set()


def get_template_items(title, db):
    return {
        "links": db.get_header_links(),
        "image": get_pfp_img(db),
        "title": title,
        "articles": list(db.get_header_articles(title)),
    }


def get_pfp_img(db: database.Database):
    global shown_images
    dbimg = db.get_pfp_images()
    if len(shown_images) == len(dbimg):
        shown_images = set()
    folder = set(dbimg).difference(shown_images)
    choice = random.choice(list(folder))
    shown_images.add(choice)
    return choice


@app.route("/~")
@app.route("/")
def index():
    with database.Database() as db:
        with open(os.path.join("static", "index.md"), "r") as f:
            return flask.render_template(
                "index.html.j2",
                **get_template_items("Index", db),
                markdown=parser.parse_text(f.read())[0],
                featured_articles=db.get_featured_articles(),
            )


@app.route("/article")
def get_article_from_id():
    article_id = flask.request.args.get("id", type=int)
    with database.Database() as db:
        try:
            category_name, title, dt, parsed, headers, embed_d, embed_i = parser.get_article_from_id(db, article_id)
        except TypeError:
            flask.abort(404)
            return
        return flask.render_template(
            "article.html.j2",
            **get_template_items(title, db),
            md_html=parsed,
            contents_html=headers,
            dt="Published: " + str(dt),
            category=category_name,
            othercategories=db.get_categories_not(category_name),
            related=db.get_similar_articles_from_id(category_name, article_id),
            embed_desc=embed_d,
            embed_img=embed_i
        )


@app.route("/articles")
def get_articles():
    with database.Database() as db:
        all_ = db.get_all_articles()
        tree = {}
        for id_, title, dt, category in all_:
            if category not in tree.keys():
                tree[category] = [(id_, title, dt)]
            else:
                tree[category].append((id_, title, str(dt)))

        return flask.render_template(
            "articles.html.j2",
            **get_template_items("Articles", db),
            tree=tree
        )


@app.route("/robots.txt")
def robots():
    return flask.send_from_directory("static", "robots.txt")


@app.route('/<string:param>')
def redirect_code(param):
    with database.Database() as db:
        url = db.get_redirect_url(param)
        if url is not None:
            return redirect(url[0])
        flask.abort(404)
        return


@app.route("/discord")
def discord():
    with database.Database() as db:
        return flask.render_template(
            "discord.html.j2",
            **get_template_items("discord", db),
            discord=CONFIG["discord"]["username"]
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


@app.route("/article/<string:name>")
def get_article_from_name(name):
    name = str.lower(name)
    with database.Database() as db:
        try:
            category_name, title, dt, parsed, headers, embed_d, embed_i = parser.get_article_from_name(db, name)
        except TypeError:
            flask.abort(404)
            return
        return flask.render_template(
            "article.html.j2",
            **get_template_items(title, db),
            md_html=parsed,
            contents_html=headers,
            dt="Published: " + str(dt),
            category=category_name,
            othercategories=db.get_categories_not(category_name),
            related=db.get_similar_articles_from_name(category_name, name),
            embed_desc=embed_d,
            embed_img=embed_i
        )


if __name__ == "__main__":
    try:
        if sys.argv[1] == "--production":
            serve(TransLogger(app), host='0.0.0.0', port=6969, threads=2)
        else:
            app.run(host="0.0.0.0", port=5001, debug=True)
    except IndexError:
        app.run(host="0.0.0.0", port=5001, debug=True)
