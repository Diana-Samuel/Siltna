import psycopg2
import datetime
import random

import enc

import pyconf
conf = pyconf.read_ini("db.ini")

conn = psycopg2.connect(
                        database=conf["database"],
                        host=conf["host"],
                        user=conf["user"],
                        password=conf["password"],
                        port=conf["port"]
                       )
cursor = conn.cursor()


def randomid():
    id = random.randint(000000000,9999999999)
    if len(str(id)) != 10:
        diff = 10 - len(str(id))
        id = str(id)
        for _ in range(diff):
            id = "0" + id
    return str(id)


def checkID(id: str) -> bool:
    cursor.execute("SELECT * FROM users WHERE id = %s LIMIT 1",(id,))
    if cursor.fetchone():
        return True
    else:
        return False

def checkEmail(email: str) -> bool:
    cursor.execute("SELECT * FROM users WHERE email = %s LIMIT 1",(email,))
    if cursor.fetchone():
        return True
    else:
        return False


def getuserinfo(id: str) -> list:
    cursor.execute("SELECT * FROM users WHERE id = %s",(id))
    return cursor.fetchone()




def adduserinfo(name: str, pw: str, email: str) -> bool:
    date = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")

    id = randomid()

    hashed_pw = enc.hashpw(pw)
    email = enc.encrypt(email,date=date)
    name = enc.encrypt(name,date=date)

    if checkID(id):
        return False
    
    if checkEmail(email):
        return False
    

    try:
        cursor.execute("INSERT INTO users (id, name, email, password,verified,date) VALUES (%s,%s,%s,%s,%s,%s)",(id,name,email,hashed_pw,False,date))
        cursor.connection.commit()
        return True
    except Exception as e:
        print(f"Error inserting user: {e}")
        cursor.connection.rollback()
        return False
    



def addPhone(id: str, phone: str) -> bool:
    if not checkID(id):
        return False
    
    cursor.execute("SELECT date FROM users WHERE id = %s",(id,))
    if cursor.fetchone():
        data = cursor.fetchone()
        date = data[0]
        phone = enc.encrypt(phone,date)
        cursor.execute("INSERT INTO users (phone) VALUES (%s) WHERE ID = %s",(phone,id,))
        return True
    else:
        return False
    

def addNote(id: str, note: str) -> bool:
    if not checkID(id):
        return False
    
    cursor.execute("SELECT date FROM users WHERE id = %s",(id,))
    if cursor.fetchone():
        data = cursor.fetchone()
        date = data[0]
        note = enc.encrypt(note,date)
        cursor.execute("INSERT INTO users (note) VALUES (%s) WHERE ID = %s",(note,id,))
        return True
    else:
        return False

def changeVerifiedValue(id: str, value: bool) -> bool:
    if not checkID(id):
        return False
    try:    
        cursor.execute("INSERT INTO users (verified) VALUES (%s) WHERE ID = %s",(value,id,))
        return True
    except:
        return False
