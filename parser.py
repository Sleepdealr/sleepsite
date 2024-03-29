#!/usr/bin/env python3

from urllib.parse import urlparse
import urllib.parse
import database
import argparse
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


def get_article_from_name(db, name):
    category_name, title, dt, markdown, embed_desc, embed_img, updt = db.get_article_from_name(name)
    html, headers = parse_text(markdown)
    return category_name, title, dt, html, headers, embed_desc, embed_img, updt


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
            urllib.parse.unquote_plus(node.attrib["id"]),
            level,  # -horrible hack
            "#%s" % node.attrib["id"])
        )

    headers = [(i[0], i[1] - thesmallestlevel, i[2]) for i in headers]

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
    subparse.add_parser("list", help="List all the markdowns in the database")

    for s in [save_parser, echo_parser, update_parser]:
        s.add_argument(
            "-m", "--markdown",
            help="Path to a markdown file",
            type=str,
            required=True
        )

    update_parser.add_argument(
        "-i", "--id",
        help="Article's id",
        type=int,
        required=True
    )

    save_parser.add_argument(
        "-c", "--category",
        help="Article category name",
        type=str,
        required=True
    )

    save_parser.add_argument(
        "-t", "--title",
        help="Article title",
        type=str,
        required=True
    )

    args = vars(p.parse_args())

    try:
        verb = sys.argv[1]
    except IndexError:
        print("No verb specified... Nothing to do... Exiting...")
        exit()

    if verb in ["save", "update", "list"]:
        with database.Database() as db:
            if verb == "save":
                if db.add_category(args["category"]):
                    print("Added category...")
                with open(args["markdown"], "r") as f:
                    db.add_article(args["category"], args["title"], f.read())
                print("Added thought...")

            elif verb == "update":
                with open(args["markdown"], "r") as f:
                    db.update_article_markdown(args["id"], f.read())

            elif verb == "list":
                for id_, title, dt, category_name in db.get_all_articles():
                    print("%d\t%-12s\t%-25s\t%s" % (id_, title, dt, category_name))

    elif verb == "echo":
        print(parse_file(args["markdown"]))


if __name__ == "__main__":
    main()
