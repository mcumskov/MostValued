import sqlite3
import os


# DataBase storage
class dbHelper:
    def __init__(self, logger):
        self.file = os.path.dirname(os.path.realpath(
            __file__))+"\\..\\database\\storage.db"
        self.logger = logger

        if self.testConnection():
            self.initDB()

    def initDB(self):
        try:
            self.execute(
                'CREATE TABLE IF NOT EXISTS scanned (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, system TEXT NOT NULL, CONSTRAINT body_system UNIQUE (name, system));')  # table scanned
        except sqlite3.Error as error:
            self.logger.error("DB error: "+str(error))
        return

    def testConnection(self):
        return self.execute()

    def execute(self, query=None, params=None):
        response = []
        try:
            conn = sqlite3.connect(self.file)
            self.logger.debug("DB connected")
            cursor = conn.cursor()

            self.logger.info("DB query: "+str(query)+" "+str(params))
            if query:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                if "select" in query.lower():
                    response = cursor.fetchall()
                else:
                    conn.commit()
                    response = True
            else:
                response = True

        except sqlite3.Error as error:
            self.logger.error("DB error: "+str(error))
            response = False
        finally:
            self.logger.info('DB result: '+str(response))
            if cursor:
                cursor.close()
            if conn:
                conn.close()
                self.logger.debug("DB disconnected")

        return response
