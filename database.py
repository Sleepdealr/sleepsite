import configparser
import pymysql
from dataclasses import dataclass



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
            self.__connection = pymysql.connect(
                **config["mysql"],
                charset = "utf8mb4"
            )
        else:
            self.__connection - pymysql.connect(
                user = self.user,
                passwd= self.passwd,
                host = config["mysql"]["host"],
                db = config["mysql"]["db"],
                charset = "utf8mb4"
           )
        return self

    def __exit__(self, type, value, traceback):
        self.__connection.close()

    def get_image(self, imageName):
        return "xyz"

if __name__ == "__main__":
    with Database() as db:
        print(db.g)
