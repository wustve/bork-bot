import os
import psycopg2

#from  dotenv import load_dotenv
#load_dotenv()
class Db():
    def __init__(self):
        self.connection = psycopg2.connect(os.environ['DATABASE_URL'], sslmode = 'require')
        self.cursor = self.connection.cursor()
    def request(self, query, requestType):
        count = 0
        while count < 5:
            try:
                if not isinstance(query, str):
                    self.cursor.execute(*query)
                else:
                    self.cursor.execute(query)
                if requestType == "fetchone":
                    return self.cursor.fetchone()
                elif requestType == "fetchall":
                    return self.cursor.fetchall()
                elif requestType == "change":
                    return
            except psycopg2.OperationalError:
                self.__init__()
                count +=1
                continue
        raise ConnectionError
