import configparser
from dataclasses import dataclass
import datetime
import psycopg2


@dataclass
class Database:
    safeLogin: bool = True
    user: str = None
    passwd: str = None

    def __enter__(self):
        config = configparser.ConfigParser()
        config.read("sleepweb.conf")
        if self.safeLogin:
            self.__connection = psycopg2.connect(
                **config["postgres"],
                port='5432'
            )
        else:
            self.__connection = psycopg2.connect(
                user=self.user,
                password=self.passwd,
                database=config["postgres"]["database"],
                host=config["postgres"]["host"],
                port='5432'
            )
        return self

    def __exit__(self, type, value, traceback):
        self.__connection.close()

    def get_header_links(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT name, link FROM headerLinks ORDER BY name;")
            return cursor.fetchall()

    def get_header_articles(self, title):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT articleName, link FROM headerArticles WHERE articleName NOT LIKE %s;", (title,))
            return cursor.fetchall()

    def get_pfp_images(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT alt, url FROM images WHERE pfp_image = true")
            xyz = cursor.fetchall()
            return xyz

    def add_article(self, category, title, markdown):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            INSERT INTO articles (article_id, category_id, title, markdown_text, dt)
            VALUES ( (SELECT MAX(article_id) + 1 FROM articles ), %s, %s, %s, %s);""",
                           (category, title, markdown, datetime.datetime.now().replace(microsecond=0)))
        self.__connection.commit()

    def get_article_from_name(self, name):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT categories.category_name, articles.title, articles.dt, articles.markdown_text, articles.embed_desc, articles.embed_img, articles.updt
            FROM articles INNER JOIN categories
            ON articles.category_id = categories.category_id
            WHERE lower(title) = %s;""", (name,))
            return cursor.fetchone()

    def get_featured_articles(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT article_id, title FROM articles WHERE featured = 1;")
            return cursor.fetchall()

    def get_all_categories(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT category_name FROM categories;")
            return [i[0] for i in cursor.fetchall()]

    def add_category(self, category):
        if not category in self.get_all_categories():
            with self.__connection.cursor() as cursor:
                cursor.execute("INSERT INTO categories (category_name) VALUES (%s);", (category,))
            self.__connection.commit()
            return True
        return False

    def get_similar_articles_from_name(self, category, name_):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT article_id, title, dt, category_name FROM articles
            INNER JOIN categories ON articles.category_id = categories.category_id
            WHERE category_name = %s AND lower(title) != %s;""",
                           (category, name_))
            return cursor.fetchall()

    def get_all_articles(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT article_id, title, dt, category_name FROM articles
            INNER JOIN categories ON articles.category_id = categories.category_id;
            """)
            return cursor.fetchall()

    def update_article_markdown(self, id_, markdown):
        with self.__connection.cursor() as cursor:
            cursor.execute("UPDATE articles SET markdown_text = %s , updt = %s WHERE article_id = %s;",
                           (markdown, datetime.datetime.now().replace(microsecond=0), id_))
        self.__connection.commit()

    def get_categories_not(self, category_name):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT category_name FROM categories WHERE category_name != %s;", (category_name,))
            return [i[0] for i in cursor.fetchall()]

    def get_redirect_url(self, redirect_name):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT url FROM redirects WHERE name = %s;
            """, (redirect_name,))
            return cursor.fetchone()


CONFIG = configparser.ConfigParser()
CONFIG.read("sleepweb.conf")

if __name__ == "__main__":
    with Database() as db:
        print("xyz")  # implement something
