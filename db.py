import psycopg2

import random
import json

import utils
import logs
import enc

from typing_extensions import Literal
idTypes = Literal["u","p"]
tables = {
            "u": "users",
            "p": "posts"
         }

import pyconf
config = pyconf.read_ini("db.ini")


def connect():
    conn = psycopg2.connect(
        database    =   config["database"],
        host        =   config["host"],
        user        =   config["user"],
        password    =   config["password"],
        port        =   config["port"]
    )

    return conn



def randomid(length: int) -> str:
    """
    Generates a random ID For Users,Posts,Groups, Etc. 
    Attr:
    length: int         # The length of the ID

    Output:
    ID: str             # ID with the length of Inputted Length 
    """
    
    # Create a variables that hold the max and min length of ID.
    minlen = ""
    maxlen = ""
    
    # Fill them with the range needed
    for i in range(int(length)):
        minlen += "0"
        maxlen += "9"
    
    # Create a random userID In the Needed Range
    userId = random.randint(int(minlen),int(maxlen))

    # If the length isn't the length given then fill the gap with "0"
    if len(str(userId)) != length:
        diff = length - len(str(userId))
        userId = str(userId)
        for _ in range(diff):
            userId = "0" + str(userId)
    
    return userId


def toDict(data: tuple, dataType: idTypes = "u") -> dict:
    """
    Takes Data comes from Database and turn it to a Dictionary for better usability
    
    Input: 
    data:   tuple               # Data that comes from the DataBase
    type:   u: Users            # Type of Data 
            p: Posts
            g: Groups  
    """

    # Check if data is empty
    if len(data) <= 0:
        return {}
    
    if dataType == "u":
        # Divide User data to pieces
        userId      = data[0]   # UserID
        name        = data[1]   # Name of User
        email       = data[2]   # Email
        password    = data[4]   # Password
        phone       = data[5]   # Phone Number
        verified    = data[6]   # If user is verified
        note        = data[7]   # Note added by admins
        profilepic  = data[-3]  # Profile Picture of User
        date        = data[-2]  # Date of creation
        following   = data[-1]  # Pages Followed By user

        userDict =  {
                        "id": userId,
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "password": password,
                        "verified": verified,
                        "note": note,
                        "profilePic": profilepic,
                        "date": date,
                        "following": following
                    }
        return userDict

    if dataType == "p":
        # Divide Post data to Pieces
        postId      = data[0]   # Post Id
        posterId    = data[1]   # Poster ID
        text        = data[2]   # Text (if there)
        images      = data[3]   # Image (if there)
        note        = data[4]   # Note
        status      = data[-4]  # Status of Post
        date        = data[-3]  # Data Created
        detailedDate= date[-2]  # More Detailes Of the Date
        tags        = data[-1]  # Tags for ALG

        postDict =  {
                        "postId": postId,
                        "posterId": posterId,
                        "text": text,
                        "images": images,
                        "note": note,
                        "status": status,
                        "date": date,
                        "detailedDate": detailedDate,
                        "tags": tags
                    }
        
        return postDict
    

def checkID(ID: str, idType: idTypes = "u") -> bool:
    """
    Check The ID if Exists in Users, Posts, etc...

    Input:
    ID:     str                 # ID To check the validity
    idType: u: Users            # ID Type 
            p: Posts
            g: Groups
    """

    # Create new Database Connection
    conn = connect()

    # Loop to Prevent Any Connection Errors
    while True:
        try:
            # Create a new Cursor
            with conn.cursor() as cursor:
                # Execute Search ID SQL Command
                cursor.execute(f"SELECT * FROM {tables[idType]} WHERE id = %s LIMIT 1",(ID,))

                # Try to fetch The ID
                if cursor.fetchone():
                    conn.close()
                    return True
                else:
                    conn.close()
                    return False
                
        # Check for Programming Errors
        except psycopg2.ProgrammingError as e:
            logs.addLog(f"[db.checkID] psycopg2.ProgrammingError {e}")
            conn.rollback()
            conn.close()
            return False
        
        # Check for connection Errors
        except psycopg2.OperationalError:
            conn = connect()
        except psycopg2.InterfaceError:
            conn = connect()
    
        # Check for Unknown Exceptions
        except Exception as e:
            logs.addLog(f"[db.checkID] Unknown Exception {e}")
            conn.rollback()
            conn.close()
            return False




"""
USER TABLE CONTENT
"""

def checkEmail(email: str) -> bool:
    """
    Check If Email already Exists in Account or Not in the Users table
    Input:
    email:  str                 # Email needed for checking

    Output:
    status: bool                # The status if email exists (True) or Not (False)
    """

    # Create new Connection with the Database
    conn = connect()

    # Loop to prevent Connection Errors
    while True:
        try:
            # Create a new Cursor
            with conn.cursor() as cursor:
                # Execute Search ID SQL Command
                cursor.execute("SELECT * FROM users WHERE email = %s LIMIT 1",(email,))

                # Try to fetch Email
                if cursor.fetchone():
                    conn.close()
                    return True
                else:
                    conn.close()
                    return False
                
        # Check for Programming Errors
        except psycopg2.ProgrammingError:
            logs.addLog(f"[db.checkEmail] psycopg2.ProgrammingError {e}")
            conn.rollback()
            conn.close()
            return False
        
        # Check for connection Errors
        except psycopg2.OperationalError:
            conn = connect()
        except psycopg2.InterfaceError:
            conn = connect()
        
        # Check for Unknown Exceptions
        except Exception as e:
            logs.addLog(f"[db.checkEmail] Unknown Exception {e}")
            conn.rollback()
            conn.close()
            return False
        


def getUserInfo(userId: str | None = None, email: str | None = None, useEmail: bool = False) -> dict:
    """
    Get The user Info by Using the UserID
    
    Input:
    usedId:     str                 # User ID Needed for the Informations
    email:      str                 # Email (Optional) used to get The UserInfo
    useEmail:   bool                # check if to use Email Instead

    Output:     dict                # Dictionary With all User Informations
    """

    # Create a New Connection with the database
    conn = connect()

    # Loop to Prevent Connection Errors
    while True:
        try:
            # Check if Id used or Email
            if userId:
                # Check if the ID Already Exists and if not returns empty
                if not checkID(userId):
                    conn.close()
                    return {}
                
                # Create a new Cursor
                with conn.cursor() as cursor:
                    # Select User Informations from the users table
                    cursor.execute("SELECT * FROM users WHERE id = %s LIMIT 1",(userId,))
                    data = cursor.fetchone()
                    conn.close()
                    return toDict(data)
            
            if useEmail:
                # Check if the Email Already Exists and if not returns empty
                if not checkEmail(email):
                    conn.close()
                    return {}
                
                # Create a new Cursor
                with conn.cursor() as cursor:
                    # Select User Informations from the users table
                    cursor.execute("SELECT * FROM users WHERE email = %s LIMIT 1",(email,))
                    data = cursor.fetchone()
                    conn.close()
                    return toDict(data)
                
        # Handle Programming Errors
        except psycopg2.ProgrammingError as e:
            logs.addLog(f"[db.getUserInfo] psycopg2.ProgrammingError :{e}")
            conn.rollback()
            conn.close()
            return {}

        # Handle Connection Errors
        except psycopg2.OperationalError:
            conn = connect()
        except psycopg2.InterfaceError:
            conn = connect()

        # Handle Unexpected Exceptions
        except Exception as e:
            logs.addLog(f"[db.getUserInfo] Unknown Exception: {e}")
            conn.rollback()
            conn.close()
            return {}
        


def addUserInfo(name: str, password: str, email: str) -> tuple[bool, str | None]:
    """
    Adds User information to the DataBase

    Input:
    name:       str             # The name of the user
    password:   str             # The password of the user
    email:      str             # The email of the user

    Output:
    status:     bool            # Status of submitting
    value:      str             # If any error happened it will be there else It will return None 
    """

    # Create a new connection with the Database
    conn = connect()

    # Loop to prevent any Connection Errors
    while True:
        try:
            # Loop to make sure unused ID created
            while True:
                # Create new 10 length userId
                userId = randomid(10)

                # Check if Exists or not
                if not checkID(userId,"u"):
                    break
            
            # Get the now time
            date = utils.timenow()

            # Check if Informations Added Already Exists or not
            if checkID(userId,"u"):
                conn.close()
                return False, "The User ID Already Exists"
            
            if checkEmail(email,"u"):
                conn.close()
                return False, "The Email Address Already Exists"
            
            # Hash the password
            hashedPassword = enc.hashpw(password)

            # Encrypt The name
            name = enc.encrypt(name,date,"u")

            # Create a new cursor
            with conn.cursor() as cursor:
                # Insert the values to the DataBase
                cursor.execute("INSERT INTO users (id, name, email, password, verified, date, following) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                                (userId ,name ,email ,hashedPassword ,False ,date ,[],))
                
                # Commit the changes
                conn.commit()

                # Create Interests to User
                # TODO ADD INTEREST TO USER USING FUNCTION CALLED createInterest(userId)

                conn.close()
                return True, None

        # Handle Programming Errors
        except psycopg2.ProgrammingError as e:
            logs.addLog(f"[db.addUserInfo] psycopg.ProgrammingError {e}")
            conn.rollback()
            conn.close()
            return False, None
        
        # Handle Database connection issues
        except psycopg2.OperationalError:
            conn = connect()
        except psycopg2.InterfaceError:
            conn = connect()

        # Handle Unknown Errors
        except Exception as e:
            logs.addLog(f"[db.addUserInfo] Unknown Exception {e}")
            conn.rollback()
            conn.close()
            return False, None
        

def chanfeVerificationStatus(userId: str, value: bool = True) -> tuple[bool,None|str]:
    """
    Change The Value of Verification of the user

    Inputs:
    userId:     str                 # User ID need to change the value of verification
    value:      bool                # Value of verification

    Outputs:
    status:     bool                # Status if Edit Worked
    value:      str                 # If any error happened it will be there else It will return None
    """

    # Create a new connection
    conn = connect()
    
    # Loop to prevent connection Errors
    while True:
        try:
            # Create new cursor
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET verified = %s WHERE id = %s",(value, userId, ))
                conn.commit()
                conn.close()
                return True, None

        # Handle Programming Errors
        except psycopg2.ProgrammingError as e:
            logs.addLog(f"[db.verifyUser] psycopg2.ProgrammingError: {e}")
            conn.rollback()
            conn.close()
            return False, None
        
        # Handle connection Errors
        except psycopg2.OperationalError:
            conn = connect()
        except psycopg2.InterfaceError:
            conn = connect()

        # Handle Unknown Exceptions
        except Exception as e:
            logs.addLog(f"[db.verifyUser] Unknown Exception: {e}")
            conn.rollback()
            conn.close()
            return False, None
        

def checkVerified(userId: str) -> bool:
    """
    Check the verification status of the User

    Inputs:
    userId: str                     # User ID needed for checking the verification status
    
    Outputs:
    status: bool                    # Verification Status of the User 
    """

    # Create new connection
    conn = connect()

    # Loop to prevent connection Errors
    while True:
        try:
            # Create new cursor
            with conn.cursor() as cursor:
                # Check if ID Exists
                if not checkID(userId):
                    conn.close()
                    return False
                
                # Get the data from the database
                cursor.execute("SELECT * FROM users WHERE id = %s",(userId, ))
                data = cursor.fetchone()
                
                # Turn data to dictionary
                data = toDict(data)

                conn.close()
                return data["verified"]


        # Handle Programming Errors
        except psycopg2.ProgrammingError as e:
            logs.addLog(f"[db.checkVerified] psycopg2.ProgrammingError: {e}")
            conn.rollback()
            conn.close()
            return False, None
        
        # Handle connection Errors
        except psycopg2.OperationalError:
            conn = connect()
        except psycopg2.InterfaceError:
            conn = connect()

        # Handle Unknown Exceptions
        except Exception as e:
            logs.addLog(f"[db.checkVerified] Unknown Exception: {e}")
            conn.rollback()
            conn.close()
            return False, None
        
    
def addPhone(userId: str, phone: str) -> bool:
    """
    Adds Phone Number to account

    Inputs:
    userId: str                 # The user id to change the phone
    phone:  str                 # Phone Number needed to be added

    Output:
    status: bool                # Status of The operation
    """

    # Create new Connection with the Database
    conn = connect()

    # Loop to prevent Connection Errors
    while True:
        try:
            # Check if UserID Already Exists
            if not checkID(userId,"u"):
                conn.close()
                return False
                
            # Get the date creation of the user
            data = getUserInfo(userId)
            date = data["date"]

            # Encrypt the Phone number
            encPhone = enc.encrypt(phone,date,"u")

            # Create new Cursor
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO users (phone) VALUES (%s) WHERE id = %s",(encPhone, userId, ))
                conn.commit()

                conn.close()
                return True
            
        # Handle Programming Exceptions
        except psycopg2.ProgrammingError as e:
            logs.addLog(f"[db.addPhone] psycopg2.ProgrammingError: {e}")
            conn.rollback()
            conn.close()
            return False

        # Handle Connection Errors
        except psycopg2.OperationalError:
            conn = connect()
        except psycopg2.InterfaceError:
            conn = connect()

        # Handle Unknown Exceptions 
        except Exception as e:
            logs.addLog(f"[db.addPhone] Unknown Exception: {e}")
            conn.rollback()
            conn.close()
            return False
        

def addPhone(userId: str, note: str) -> bool:
    """
    Adds Phone Number to account

    Inputs:
    userId: str                 # The user id to change the phone
    note:  str                 # Note needed to be added

    Output:
    status: bool                # Status of The operation
    """

    # Create new Connection with the Database
    conn = connect()

    # Loop to prevent Connection Errors
    while True:
        try:
            # Check if UserID Already Exists
            if not checkID(userId,"u"):
                conn.close()
                return False
                
            # Get the date creation of the user
            data = getUserInfo(userId)
            date = data["date"]

            # Encrypt the Phone number
            encNote = enc.encrypt(note,date,"u")

            # Create new Cursor
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO users (note) VALUES (%s) WHERE id = %s",(encNote, userId, ))
                conn.commit()

                conn.close()
                return True
            
        # Handle Programming Exceptions
        except psycopg2.ProgrammingError as e:
            logs.addLog(f"[db.addNote] psycopg2.ProgrammingError: {e}")
            conn.rollback()
            conn.close()
            return False

        # Handle Connection Errors
        except psycopg2.OperationalError:
            conn = connect()
        except psycopg2.InterfaceError:
            conn = connect()

        # Handle Unknown Exceptions 
        except Exception as e:
            logs.addLog(f"[db.addNote] Unknown Exception: {e}")
            conn.rollback()
            conn.close()
            return False
        

def createPost(text: str, images: list, userId: str) -> tuple[bool, str | None]:
    """
    Create a new post and put it to the Database

    Inputs:
    text:   str                     # Text Content of the Post
    images: list                    # Image Content of the Post
    userId: str                     # User ID Of the creator of the Post
    
    Outputs:
    status: bool                    # status of adding the Post
    value:  str                     # Value of Error adding the Post
    """

    # Create a new connection with the Database
    conn = connect()

    # Loop to prevent Connection Errors
    while True:
        try:
            # Create a new POST ID
            while True:
                postId = randomid(32)
                if not checkID(postId,"p"):
                    break

            # Check if Post is Empty
            if len(images) <= 0 and len(text.strip()) <= 0:
                conn.close()
                return False, "The Post is Empty, You must Add something to the Post"
            
            # Define the type of Post
            withImages = len(images) > 0
            withText = len(text.strip()) > 0

            # Check Post Creator ID
            if not checkID(userId,"u"):
                conn.close()
                return False, "User Must Be Logged In"

            # Get the right now Date
            date = utils.timenow()

            # Encrypt Text
            if withText:
                encText = enc.encrypt(text,date,"p")

            # Encrypt Images
            encImages = []
            if withImages:
                for image in images:
                    encImages.append(enc.encryptFile(image,date))

            # Turn list into JSON
            encImages_json = json.dumps(encImages)

            # Create new cursor
            with conn.cursor() as cursor:
                try:
                    # Check the type of Post
                    if withText and withImages:
                        cursor.execute("INSERT INTO posts (id, poster_id, text, images, date,tags) VALUES (%s,%s,%s,%s,%s,%s)",
                                       (postId, userId, encText, encImages_json, date,["text","image"], ))

                    elif withText:
                        cursor.execute("INSERT INTO posts (id, poster_id, text, date,tags) VALUES (%s,%s,%s,%s,%s)",
                                       (postId, userId, encText, date,["text"], ))
                    elif withImages:
                        cursor.execute("INSERT INTO posts (id, poster_id, images, date,tags) VALUES (%s,%s,%s,%s,%s)",
                                       (postId, userId, encImages_json, date,["image"], ))
                    else:
                        conn.close()
                        return False
                    
                    # Commit Changes
                    conn.commit()
                    conn.close()
                    return True


                # Handle Programming Exceptions
                except psycopg2.ProgrammingError as e:
                    logs.addLog(f"[db.createPost] psycopg2.ProgrammingError: {e}")
                    conn.rollback()
                    conn.close()
                    return False

                # Handle Connection Errors
                except psycopg2.OperationalError:
                    conn = connect()
                except psycopg2.InterfaceError:
                    conn = connect()

                # Handle Unknown Exceptions 
                except Exception as e:
                    logs.addLog(f"[db.createPost] Unknown Exception: {e}")
                    conn.rollback()
                    conn.close()
                    return False


        # Handle Programming Exceptions
        except psycopg2.ProgrammingError as e:
            logs.addLog(f"[db.createPost] psycopg2.ProgrammingError: {e}")
            conn.rollback()
            conn.close()
            return False

        # Handle Connection Errors
        except psycopg2.OperationalError:
            conn = connect()
        except psycopg2.InterfaceError:
            conn = connect()

        # Handle Unknown Exceptions 
        except Exception as e:
            logs.addLog(f"[db.createPost] Unknown Exception: {e}")
            conn.rollback()
            conn.close()
            return False
        

def getPost(postId: str) -> tuple[bool,dict]:
    """
    Get the post details by using Post ID

    Inputs:
    postId: str                 # Post ID Needed to fetch the Post

    Outputs:
    status: bool
    value:  dict | str          # Post Details as a Dict (empty if no post found and will have error value if error occured)
    """

    # Create new connection with the Database
    conn = connect()

    # Loop to prevent Connection Errors
    while True:
        try:
            # Create new cursor
            with conn.cursor() as cursor:
                # Check if Post exists
                if checkID(postId,"p"):
                    # Execute command to fetch the Post using Post ID
                    cursor.execute("SELECT * FROM posts WHERE id = %s",(postId, ))
                    
                    # Fetch data from Database
                    data = cursor.fetchone()

                    # Turn it to Dict
                    dataDict = toDict(data,"p")

                    # Close connection with database
                    conn.close()

                    return True, dataDict

                else:
                    conn.close()
                    return False, f"Post not found: {postId}"
            
        # Handle Programming Exceptions
        except psycopg2.ProgrammingError as e:
            logs.addLog(f"[db.getPost] psycopg2.ProgrammingError: {e}")
            conn.rollback()
            conn.close()
            return False

        # Handle Connection Errors
        except psycopg2.OperationalError:
            conn = connect()
        except psycopg2.InterfaceError:
            conn = connect()

        # Handle Unknown Exceptions 
        except Exception as e:
            logs.addLog(f"[db.getPost] Unknown Exception: {e}")
            conn.rollback()
            conn.close()
            return False
        

def getRandomPosts(limit: int =20) -> list:
    """
    Get Random Posts From the Database

    Inputs:
    limit:  int                 # Maximum number of posts to retrieve from Database

    Outputs:
    Posts:  list                # List of Posts Retrieved by Database
    """

    # Create new connection with the Database
    conn = connect()

    # Loop to prevent Connection Errors
    while True:
        try:
            # Create new cursor
            with conn.cursor() as cursor:
                # Execute a command to get Random Posts
                cursor.execute("SELECT * FROM posts ORDER BY RANDOM() LIMIT %s",
                               (limit, ))
                
                # Retrieve Data
                fetchedData = cursor.fetchall()

                # Turn fetched data to more organized list
                data = []
                for post in fetchedData:
                    data.append(toDict(post,"p"))

                # Close Connection with Database
                conn.close()

                return data
            
        # Handle Programming Exceptions
        except psycopg2.ProgrammingError as e:
            logs.addLog(f"[db.getRandomPosts] psycopg2.ProgrammingError: {e}")
            conn.rollback()
            conn.close()
            return False

        # Handle Connection Errors
        except psycopg2.OperationalError:
            conn = connect()
        except psycopg2.InterfaceError:
            conn = connect()

        # Handle Unknown Exceptions 
        except Exception as e:
            logs.addLog(f"[db.getRandomPosts] Unknown Exception: {e}")
            conn.rollback()
            conn.close()
            return False
        

def createInterest(userId: str) -> bool:
    """
    Create Interest For the user

    Inputs:
    userId: str                     # User ID needed for Interest Creation

    Outputs:
    status: bool                    # Status of interest Creation
    """

    # Create new connection with Database
    conn = connect()

    # Loop to Prevent Connection Errors
    while True:
        try:
            # Check if userId Exists
            if not checkID(userId,"u"):
                conn.clsoe()
                return False, "User ID Does Not Exists"

            # Create new cursor
            with conn.cursor() as cursor:
                # Add Empty Interests
                cursor.execute("INSERT INTO interests (userId, tags) VALUES (%s,%s)",
                               (userId,[]))
                
                # Commit changes
                conn.commit()

                conn.close()

                return True
            
        # Handle Programming Exceptions
        except psycopg2.ProgrammingError as e:
            logs.addLog(f"[db.createInterest] psycopg2.ProgrammingError: {e}")
            conn.rollback()
            conn.close()
            return False

        # Handle Connection Errors
        except psycopg2.OperationalError:
            conn = connect()
        except psycopg2.InterfaceError:
            conn = connect()

        # Handle Unknown Exceptions 
        except Exception as e:
            logs.addLog(f"[db.createInterest] Unknown Exception: {e}")
            conn.rollback()
            conn.close()
            return False
        

def getInterests(userId: str) -> list:
    """
    Get the Interests of the User

    Inputs:
    userId:     str                     # User ID Needed for Interests Retrieval
    
    Outputs:
    Interests:  list                    # List of Interests (empty if failed or None)
    """

    # Create new Connection with Database
    conn = connect()

    # Loop to Prevent Connection Errors
    while True:
        try:
            # Check if user ID Exists
            if not checkID(userId,"u"):
                conn.close()
                return []
            
            # Create new cursor
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM interests WHERE userId = %s",
                               (userId, ))
                
                data = cursor.fetchone()
                tags = data[1]

                conn.close()
                return tags


        except psycopg2.ProgrammingError as e:
            logs.addLog(f"[db.getInterest] psycopg2.ProgrammingError: {e}")
            conn.rollback()
            conn.close()
            return False

        # Handle Connection Errors
        except psycopg2.OperationalError:
            conn = connect()
        except psycopg2.InterfaceError:
            conn = connect()

        # Handle Unknown Exceptions 
        except Exception as e:
            logs.addLog(f"[db.getInterest] Unknown Exception: {e}")
            conn.rollback()
            conn.close()
            return False
        


def getInterests(interest: str,userId: str) -> bool:
    """
    Get the Interests of the User

    Inputs:
    userId:     str                     # User ID Needed for Interests Retrieval
    
    Outputs:
    Interests:  list                    # List of Interests (empty if failed or None)
    """

    # Create new Connection with Database
    conn = connect()

    # Loop to Prevent Connection Errors
    while True:
        try:
            # Check if user ID Exists
            if not checkID(userId,"u"):
                conn.close()
                return []
            
            # Create new cursor to get Current Interests
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM interests WHERE userId = %s",
                               (userId, ))
                
                data = cursor.fetchone()
                tags = data[1]

            tags.append(interest)

            # Create new cursor
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO interests (tags) VALUES (%s) WHERE userId = %s",
                               (tags, userId, ))
                
                # Commit changes
                conn.commit()

                conn.close()
                return True


        except psycopg2.ProgrammingError as e:
            logs.addLog(f"[db.getInterest] psycopg2.ProgrammingError: {e}")
            conn.rollback()
            conn.close()
            return False

        # Handle Connection Errors
        except psycopg2.OperationalError:
            conn = connect()
        except psycopg2.InterfaceError:
            conn = connect()

        # Handle Unknown Exceptions 
        except Exception as e:
            logs.addLog(f"[db.getInterest] Unknown Exception: {e}")
            conn.rollback()
            conn.close()
            return False