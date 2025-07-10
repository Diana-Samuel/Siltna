import psycopg2

import datetime
import random
import json

import enc

import pyconf

from typing_extensions import Literal
conf = pyconf.read_ini("db.ini")

userconn = psycopg2.connect(
                        database=conf["database"],
                        host=conf["host"],
                        user=conf["user"],
                        password=conf["password"],
                        port=conf["port"]
                       )

def conn():
    global userconn,usercursor
    userconn = psycopg2.connect(
                            database=conf["database"],
                            host=conf["host"],
                            user=conf["user"],
                            password=conf["password"],
                            port=conf["port"]
                        )

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

def checkID(user_id: str,idtype: Literal["u","p"] = "u") -> bool:
    while True:
        if idtype == "u":
            table = "users"
        elif idtype == "p":
            table = "posts"
        else:
            table = "users"
        try:
            with userconn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table} WHERE id = %s LIMIT 1",(user_id,))

                if cursor.fetchone():
                    return True
                else:
                    return False
        except psycopg2.ProgrammingError as e:
            print(f"psycopg2.ProgrammingError: {e}")
            return False
        except psycopg2.OperationalError:
            conn()
        except psycopg2.InterfaceError:
            conn()


"""
USER TABLE CONTENT
"""
def checkEmail(email: str) -> bool:
    while True:
        try:
            with userconn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s LIMIT 1",(email,))
                try:
                    if cursor.fetchone():
                        return True
                    else:
                        return False
                except psycopg2.ProgrammingError:
                    return False
        except psycopg2.OperationalError:
            conn()
        except psycopg2.InterfaceError:
            conn()


def getuserinfo(user_id: str) -> list:
    while True:
        try:
            with userconn.cursor() as cursor:
                try:
                    cursor.execute("SELECT * FROM users WHERE id = %s",(user_id, ))
                    return cursor.fetchone()
                except psycopg2.OperationalError:
                    conn()
                except Exception as e:
                    print("Database Error: {e}")
                    cursor.connection.rollback()
                    raise
        except psycopg2.OperationalError:
            conn()
        except psycopg2.InterfaceError:
            conn()

def getuserinfo_byemail(email: str) -> list:
    while True:
        try:
            with userconn.cursor() as cursor:
                try:
                    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                    data = cursor.fetchone()
                    if data:
                        return data
                    else:
                        raise ValueError("Cannot find the email address")
                except psycopg2.OperationalError:
                    conn()
                except Exception as e:
                    print(f"Database error: {e}")
                    cursor.connection.rollback()
                    raise
        except psycopg2.OperationalError:
            conn()
        except psycopg2.InterfaceError:
            conn()


def adduserinfo(name: str, pw: str, email: str) -> bool:
    while True:
        try:
            date = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
            while True:
                user_id = randomid(10)
                if not checkID(user_id, "u"):
                    break

            hashed_pw = enc.hashpw(pw)
            name = enc.encrypt(name,date=date,encType="u")

            if checkID(user_id):
                return False, None
            
            if checkEmail(email):
                return False, None
            
            with userconn.cursor() as cursor:
                try:
                    cursor.execute("INSERT INTO users (id, name, email, password,verified,date,following) VALUES (%s,%s,%s,%s,%s,%s,%s)",(user_id,name,email,hashed_pw,False,date,[],))
                    cursor.connection.commit()
                    createInterest(user_id)
                    return True, user_id
                except psycopg2.OperationalError:
                    conn()
                except Exception as e:
                    print(f"Error inserting user: {e}")
                    cursor.connection.rollback()
                    return False, None
        except psycopg2.OperationalError:
            conn()
        except psycopg2.InterfaceError:
            conn()
    

def verify(userid:str) -> bool:
    while True:
        with userconn.cursor() as cursor:
            try:
                cursor.execute("UPDATE users SET verifed = True WHERE id = %s",(userid, ))
                cursor.connection.commit()
            except psycopg2.OperationalError:
                conn()
            except psycopg2.InterfaceError:
                conn()
            except Exception as e:
                raise e

def checkVerified(userid: str) -> bool:
    while True:
        with userconn.cursor() as cursor:
            try:
                cursor.execute("SELECT * FROM users WHERE id = %s",(userid, ))
                verified = cursor.fetchone()[5]
                return verified
            except psycopg2.OperationalError:
                conn()
            except psycopg2.InterfaceError:
                conn()            
            except:
                return False

def addPhone(user_id: str, phone: str) -> bool:
    while True:
        try:
            with userconn.cursor() as cursor:
                if not checkID(user_id):
                    return False
                
                cursor.execute("SELECT date FROM users WHERE id = %s",(user_id,))
                if cursor.fetchone():
                    data = cursor.fetchone()
                    date = data[-2]
                    phone = enc.encrypt(phone,date,encType="u")
                    cursor.execute("INSERT INTO users (phone) VALUES (%s) WHERE ID = %s",(phone,user_id,))
                    return True
                else:
                    return False
        except psycopg2.OperationalError:
            conn()
        except psycopg2.InterfaceError:
            conn()

def addNote(user_id: str, note: str) -> bool:
    while True:
        try:
            with userconn.cursor() as cursor:
                if not checkID(user_id):
                    return False
                
                cursor.execute("SELECT date FROM users WHERE id = %s",(user_id,))
                if cursor.fetchone():
                    data = cursor.fetchone()
                    date = data[-2]
                    note = enc.encrypt(note,date,encType="u")
                    cursor.execute("INSERT INTO users (note) VALUES (%s) WHERE ID = %s",(note,user_id,))
                    return True
                else:
                    return False
        except psycopg2.OperationalError:
            conn()
        except psycopg2.InterfaceError:
            conn()

def changeVerifiedValue(user_id: str, value: bool) -> bool:
    while True:
        try:
            with userconn.cursor() as cursor:
                if not checkID(user_id):
                    return False
                try:    
                    cursor.execute("INSERT INTO users (verified) VALUES (%s) WHERE ID = %s",(value,user_id,))
                    return True
                except:
                    return False
        except psycopg2.OperationalError:
            conn()
        except psycopg2.InterfaceError:
            conn()
"""
-------------------------------------------------------------------------------------------------------------------
"""




"""
POST TABLE CONTENT
"""

def createPost(text: str, images: list, userid: str) -> bool:
    while True:
        while True:
            postid = randomid(32)
            if not checkID(postid, "p"):
                break
        if len(images) <= 0 and len(text.strip()) <= 0:
            return False
        withImages = len(images) > 0
        withText = len(text) > 0

        if not checkID(userid, "u"):
            return False

        date = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")

        encText = None
        if withText:
            encText = enc.encrypt(text, date, "p")

        encImages = []
        if withImages:
            for i in images:
                encrypted_file_path = enc.encryptFile(i, date)
                encImages.append(encrypted_file_path)
        encImages_json = json.dumps(encImages)
        with userconn.cursor() as cursor:
            try:
                if withText and withImages:
                    cursor.execute("INSERT INTO posts (id, poster_id, text, images, date,tags) VALUES (%s,%s,%s,%s,%s,%s)", (postid, userid, encText, encImages_json, date,["text","image"]))
                elif withText:
                    cursor.execute("INSERT INTO posts (id, poster_id, text, date,tags) VALUES (%s,%s,%s,%s,%s)", (postid, userid, encText, date,["text"]))
                elif withImages:
                    cursor.execute("INSERT INTO posts (id, poster_id, images, date,tags) VALUES (%s,%s,%s,%s,%s)", (postid, userid, encImages_json, date,["image"]))
                else:
                    return False
                cursor.connection.commit()
                return True
            except psycopg2.OperationalError:
                conn()
            except psycopg2.InterfaceError:
                conn()
            except Exception as e:
                cursor.connection.rollback()
                return False


def getRandomPosts(limit=20):
    while True:
        try:
            with userconn.cursor() as cursor:
                cursor.execute("SELECT * FROM posts ORDER BY RANDOM() LIMIT %s",(limit,))
                rawdata = cursor.fetchall()
                data = []
                for i in rawdata:
                    temp = []
                    for j in i:
                        temp.append(j)
                    data.append(temp)

                return data
        except psycopg2.OperationalError:
            conn()
        except psycopg2.InterfaceError:
            conn()

def getPost(postid:str) -> list:
    while True:
        try:
            with userconn.cursor() as cursor:
                if checkID(postid,idtype="p"):
                    cursor.execute("SELECT * FROM posts WHERE id = %s",(postid,))
                    data = cursor.fetchone()
                    l = []
                    for i in data:
                        l.append(i)
                    return True,l
                else:
                    return False,f"Post Not Found {postid}"
        except psycopg2.OperationalError:
            conn()
        except psycopg2.InterfaceError:
            conn()
        except Exception as e:
            return False, str(e)


"""
Interests Table (algorithm)
"""
def createInterest(userid):
    while True:
        try:
            with userconn.cursor() as cursor:
                if checkID(userid,"u"):
                    cursor.execute("INSERT INTO interests (userId,tags) VALUES (%s,%s)",(userid,[]))
                    cursor.connection.commit()
                    return True
        except psycopg2.OperationalError:
            conn()
        except psycopg2.InterfaceError:
            conn()
        except Exception as e:
            print(f"[Create Interest] Error: {e}")
            return False

def addInterest(userid: str, interest: str) -> bool:
    while True:
        try:
            with userconn.cursor() as cursor:
                if checkID(userid,"u"):
                    cursor.execute("SELECT * FROM interests WHERE userId = %s",userid)
                else:
                    raise KeyError("Couldn't Find User assotiated with that ID")
                data = cursor.fetchone()
                tags = data[1]
                tags.append(interest)
                cursor.execute("INSERT INTO interests (tags) VALUES (%s) WHERE userId = %s",(tags,userid,))
                cursor.connection.commit()
                return True
        except psycopg2.OperationalError:
            conn()
        except psycopg2.InterfaceError:
            conn()
        except Exception as e:
            print(f"[Add Interest] Error adding interests: {e}")
            return False

def getInterests(userid: str) -> list:
    while True:
        try:
            with userconn.cursor() as cursor:
                if checkID(userid,"u"):
                    cursor.execute("SELECT * FROM interests WHERE userId = %s", (userid,))
                else:
                    raise KeyError("Couldn't Find User assotiated with that ID")
                data = cursor.fetchone()
                tags = data[1]
                return tags
        except psycopg2.OperationalError:
            conn()
        except psycopg2.InterfaceError:
            conn()