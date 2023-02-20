#!/usr/bin/env python3

from urllib.parse import urlparse
import urllib.parse
import database
import argparse
import getpass
import application as app
import sys
import mistune
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
import lxml.etree
import lxml.html
import jinja2
import houdini


class HighlightRenderer(mistune.HTMLRenderer):
    def blockcode(self, text, lang):
        try:
            lexer = get_lexer_by_name(lang, stripall=True)
        except ClassNotFound:
            lexer = None

        if lexer:
            formatter = HtmlFormatter()
            return highlight(text, lexer, formatter)
        # default
        return '\n<pre><code>{}</code></pre>\n'.format(houdini.escape_html(text.strip()))

    def block_quote(self, content):
        content = content[3:-5]
        out = '\n<blockquote>'
        for line in houdini.escape_html(content.strip()).split("\n"):
            out += '\n<span class="quote">{}</span><br>'.format(line)
        return out + '\n</blockquote>'

    def heading(self, text, level):
        hash_ = urllib.parse.quote_plus(text)
        return "<h%d id='%s'>%s <a class='header_linker' href='#%s'>[#]</a></h%d>" % (
            level, hash_, text, hash_, level
        )


def get_article_from_id(db, id_):
    category_name, title, dt, markdown, embed_desc, embed_img = db.get_article_from_id(id_)
    html, headers = parse_text(markdown)
    return category_name, title, dt, html, headers, embed_desc, embed_img


def get_article_from_name(db, name):
    category_name, title, dt, markdown, embed_desc, embed_img = db.get_article_from_name(name)
    html, headers = parse_text(markdown)
    return category_name, title, dt, html, headers, embed_desc, embed_img


def parse_file(path):
    with open(path, "r") as f:
        unformatted = f.read()

    return parse_text(unformatted)


def parse_text(unformatted):
    md = mistune.create_markdown(
        renderer=HighlightRenderer(),
        plugins=["strikethrough", "table", "url", "task_lists", "def_list"]
    )
    html = md(unformatted)
    return html, get_headers(html)


def get_headers(html):
    root = lxml.html.fromstring(html)

    headers = []
    thesmallestlevel = 7
    for node in root.xpath('//h1|//h2|//h3|//h4|//h5//h6'):
        level = int(node.tag[-1])
        if level < thesmallestlevel:
            thesmallestlevel = level
        headers.append((
            # lxml.etree.tostring(node),
            # "<p>%s</p>" % urllib.parse.unquote_plus(node.attrib["id"]),     # possibly insecure?
            urllib.parse.unquote_plus(node.attrib["id"]),
            level,  # -horrible hack
            "#%s" % node.attrib["id"])
        )

    headers = [(i[0], i[1] - thesmallestlevel, i[2]) for i in headers]
    # print(headers)
    # there is a bug here-
    # it must start with the largest header and only go up and down in increments of one
    #       TODO: fix it!
    md_template = jinja2.Template("""
{% for text, depth, link in contents %}
{{ "    " * depth }} - [{{ text }}]({{ link }})
{% endfor %}
    """)

    return mistune.html(md_template.render(contents=headers))


def main():
    p = argparse.ArgumentParser()
    subparse = p.add_subparsers(help="sub-command help")
    save_parser = subparse.add_parser("save", help="Add a markdown file to the database")
    echo_parser = subparse.add_parser("echo", help="Print markdown render to stdout")
    update_parser = subparse.add_parser("update", help="Replace a markdown file")
    export_parser = subparse.add_parser("export", help="Export a database markdown file to disk")
    list_parser = subparse.add_parser("list", help="List all the markdowns in the database")

    for s in [save_parser, echo_parser, update_parser]:
        s.add_argument(
            "-m", "--markdown",
            help="Path to a markdown file",
            type=str,
            required=True
        )

    for s in [save_parser]:
        s.add_argument(
            "-t", "--title",
            help="Article title",
            type=str,
            required=True
        )
        s.add_argument(
            "-c", "--category",
            help="Article category",
            type=str,
            required=True
        )

    for s in [save_parser, update_parser, export_parser, list_parser]:
        s.add_argument(
            "-u", "--username",
            help="Username to use for the database",
            type=str,
            required=True
        )

    for s in [export_parser, update_parser]:
        s.add_argument(
            "-i", "--id",
            help="Article's id",
            type=int,
            required=True
        )

    export_parser.add_argument(
        "-o", "--out",
        help="Path to write the markdown file to",
        type=str,
        required=True
    )

    args = vars(p.parse_args())

    if "username" in args.keys():
        args["password"] = getpass.getpass(
            "Enter password for %s@%s: " % (args["username"], app.CONFIG["postgres"]["host"]))

    try:
        verb = sys.argv[1]
    except IndexError:
        print("No verb specified... Nothing to do... Exiting...")
        exit()

    if verb in ["save", "export", "update", "list"]:
        with database.Database(
                safeLogin=False,
                user=args["username"],
                passwd=args["password"]
        ) as db:
            if verb == "save":
                if db.add_category(args["category"]):
                    print("Added category...")
                with open(args["markdown"], "r") as f:
                    db.add_article(args["category"], args["title"], f.read())
                print("Added thought...")

            elif verb == "export":
                with open(args["out"], "w") as f:
                    f.writelines(db.get_article_from_id(args["id"])[-1])
                print("Written to %s" % args["out"])

            elif verb == "update":
                with open(args["markdown"], "r") as f:
                    db.update_thought_markdown(args["id"], f.read())

            elif verb == "list":
                for id_, title, dt, category_name in db.get_all_articles():
                    print("%d\t%s\t%s\t%s" % (id_, title, dt, category_name))

    elif verb == "echo":
        print(parse_file(args["markdown"]))


if __name__ == "__main__":
    main()
