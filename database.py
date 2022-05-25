import configparser
from dataclasses import dataclass
import psycopg2

#make it work with postgres
@dataclass
class Database:
    safeLogin: bool = True # Autologin with the user in conf file. Conf file is intentionally read only
    user: str = None
    passwd: str = None

    def __enter__(self):
        config = configparser.ConfigParser()
        config.read("sleepweb.conf")
        if self.safeLogin:
            self.__connection = psycopg2.connect(
                **config["postgres"],
                port='5433'
            )
        else:
            self.__connection = psycopg2.connect(
                user = self.user,
                password = self.passwd,
                database = config["postgres"]["database"],
                host = config["postgres"]["host"],
                port = '5433'
            )
        return self

    def __exit__(self, type, value, traceback):
        self.__connection.close()

    def get_pfp_images(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT alt, url FROM images WHERE pfp_image = true")
            xyz = cursor.fetchall()
            print(xyz)
            return xyz

    def add_article(self, category, title, markdown):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            INSERT INTO articles (category_id, title, markdown_text)
            VALUES ((
                SELECT category_id FROM categories WHERE category_name = %s
            ), %s, %s);""", (category, title, markdown))
        self.__connection.commit()

    def get_article(self, id_):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT categories.category_name, articles.title, dt, markdown_text
            FROM articles INNER JOIN categories
            ON articles.category_id = categories.category_id
            WHERE article_id = %s;""", (id_, ))
            return cursor.fetchone()

    def get_similar_articles(self, category, id_):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT article_id, title, category_name FROM articles
            INNER JOIN categories ON articles.category_id = categories.category_id
            WHERE category_name = %s AND article_id != %s;""",
            (category, id_))
            return cursor.fetchall()

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
                cursor.execute("INSERT INTO categories (category_name) VALUES (%s);", (category, ))
            self.__connection.commit()
            return True
        return False

    def get_similar_articles(self, category, id_):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT article_id, title, dt, category_name FROM articles
            INNER JOIN categories ON articles.category_id = categories.category_id
            WHERE category_name = %s AND article_id != %s;""",
            (category, id_))
            return cursor.fetchall()

    def get_all_articles(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT article_id, title, dt, category_name FROM articles
            INNER JOIN categories ON articles.category_id = categories.category_id;
            """)
            return cursor.fetchall()

    def update_thought_markdown(self, id_, markdown):
        with self.__connection.cursor() as cursor:
            cursor.execute("UPDATE articles SET markdown_text = %s WHERE article_id = %s;", (markdown, id_))
        self.__connection.commit()

    def get_categories_not(self, category_name):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT category_name FROM categories WHERE category_name != %s;", (category_name, ))
            return [i[0] for i in cursor.fetchall()]

    def get_image(self, imageName):
        return "xyz"

CONFIG = configparser.ConfigParser()
CONFIG.read("sleepweb.conf")

if __name__ == "__main__":
    with Database() as db:
        print("xyz") # implement something
