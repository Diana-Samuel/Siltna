import psycopg2
import datetime
import random

import enc

import pyconf
conf = pyconf.read_ini("db.ini")

userconn = psycopg2.connect(
                        database=conf["database"],
                        host=conf["host"],
                        user=conf["user"],
                        password=conf["password"],
                        port=conf["port"]
                       )
usercursor = userconn.cursor()


def randomid(length: int) -> str:
    minlen = ""
    maxlen = ""
    for i in range(int(length)):
        minlen += "0"
        maxlen += "9"
    user_id = random.randint(int(minlen),int(maxlen))
    if len(str(user_id)) != length:
        diff = length - len(str(user_id))
        user_id = str(user_id)
        for _ in range(diff):
            user_id = "0" + user_id
    return str(user_id)


def checkID(user_id: str) -> bool:
    usercursor.execute("SELECT * FROM users WHERE id = %s LIMIT 1",(user_id,))
    if usercursor.fetchone():
        return True
    else:
        return False

def checkEmail(email: str) -> bool:
    usercursor.execute("SELECT * FROM users WHERE email = %s LIMIT 1",(email,))
    if usercursor.fetchone():
        return True
    else:
        return False


def getuserinfo(user_id: str) -> list:
    usercursor.execute("SELECT * FROM users WHERE id = %s",(user_id, ))
    return usercursor.fetchone()

def getuserinfo_byemail(email: str) -> list:
    usercursor.execute("SELECT * FROM users WHERE email = %s",(email, ))
    return usercursor.fetchone()

def adduserinfo(name: str, pw: str, email: str) -> bool:
    date = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")

    user_id = randomid(10)

    hashed_pw = enc.hashpw(pw)
    email = enc.encrypt(email,date=date,encType="u")
    name = enc.encrypt(name,date=date,encType="u")

    if checkID(user_id):
        return False
    
    if checkEmail(email):
        return False
    

    try:
        usercursor.execute("INSERT INTO users (id, name, email, password,verified,date) VALUES (%s,%s,%s,%s,%s,%s)",(user_id,name,email,hashed_pw,False,date))
        usercursor.userconnection.commit()
        return True
    except Exception as e:
        print(f"Error inserting user: {e}")
        usercursor.userconnection.rollback()
        return False
    

def verify(userid:str) -> bool:
    try:
        usercursor.execute("UPDATE users SET verifed = True WHERE id = %s",(userid, ))
        usercursor.connection.commit()
    except Exception as e:
        raise e

def checkVerified(userid: str) -> bool:
    try:
        usercursor.execute("SELECT * FROM users WHERE id = %s",(userid, ))
        verified = usercursor.fetchone()[5]
        return verified
    except:
        return False

def addPhone(user_id: str, phone: str) -> bool:
    if not checkID(user_id):
        return False
    
    usercursor.execute("SELECT date FROM users WHERE id = %s",(user_id,))
    if usercursor.fetchone():
        data = usercursor.fetchone()
        date = data[0]
        phone = enc.encrypt(phone,date,encType="u")
        usercursor.execute("INSERT INTO users (phone) VALUES (%s) WHERE ID = %s",(phone,user_id,))
        return True
    else:
        return False
    

def addNote(user_id: str, note: str) -> bool:
    if not checkID(user_id):
        return False
    
    usercursor.execute("SELECT date FROM users WHERE id = %s",(user_id,))
    if usercursor.fetchone():
        data = usercursor.fetchone()
        date = data[0]
        note = enc.encrypt(note,date,encType="u")
        usercursor.execute("INSERT INTO users (note) VALUES (%s) WHERE ID = %s",(note,user_id,))
        return True
    else:
        return False

def changeVerifiedValue(user_id: str, value: bool) -> bool:
    if not checkID(user_id):
        return False
    try:    
        usercursor.execute("INSERT INTO users (verified) VALUES (%s) WHERE ID = %s",(value,user_id,))
        return True
    except:
        return False
