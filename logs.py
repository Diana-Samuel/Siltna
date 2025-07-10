import psycopg2

from utils import timenow

import pyconf
config = pyconf.read_ini("db.ini")

def connect():
    conn = psycopg2.connect(
        database    =   config["debugdb"],
        host        =   config["host"],
        user        =   config["user"],
        password    =   config["password"],
        port        =   config["port"]
    )

    return conn


def addLog(log: str) -> bool:
    conn = connect()
    while True:
        try:
            time = timenow()
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO logs (log,date) VALUES (%s,%s)",(log,time,))
                cursor.connection.commit()
        except psycopg2.ProgrammingError as e:
            addLog(f"[addLog] psycopg2.ProgrammingError: {e}")
            cursor.connection.rollback()
            return False
        except psycopg2.OperationalError:
            conn = connect()
        except psycopg2.InterfaceError:
            conn = connect()
