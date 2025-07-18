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
    """
    Add Logs to Debugging DataBase
    
    Inputs: 
    log:    str             # The main Logs to put in database 

    Outputs:
    status: bool            # The Status if Adding Logs Worked (True) Or Not (False)
    """

    # Create new connection with the Database
    conn = connect()

    # Loop to Make sure Connection
    while True:
        try:
            # Fetch Detailed Time
            time = timenow(ifDetailed=True)

            # Create new Cursor
            with conn.cursor() as cursor:

                # Insert Logs value to Logs Table
                cursor.execute("INSERT INTO logs (log,date) VALUES (%s,%s)",(log,time,))
                
                # Commit Changes to the Database
                conn.commit()

                # Close connection with the Database
                conn.close()

                return True
            
        # Handling Programming Errors
        except psycopg2.ProgrammingError as e:
            addLog(f"[addLog] psycopg2.ProgrammingError: {e}")
            conn.rollback()
            conn.close()
            return False
        
        # Handling Database Connection Errors
        except psycopg2.OperationalError:
            conn = connect()
        except psycopg2.InterfaceError:
            conn = connect()

        # Handling Unknown Exceptions
        except Exception as e:
            addLog(f"[addLog] Unknown Exception: {e}")
            conn.rollback()
            conn.close()
            return False