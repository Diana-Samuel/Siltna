from flask import Flask, url_for, redirect      # Handle Functions and URL Works
from flask import request, jsonify, session     # Handle APIs and Requests
from flask import render_template, send_file    # For File Handling with Flask
from flask import abort                         # Error handling with flask
from werkzeug.utils import secure_filename      # Handle File uploads
from flask_session import Session               # Advanced Flask Session
import redis                                    # For Session handling
from flask_socketio import SocketIO, emit       # Handle websocket events
from flask_socketio import join_room,leave_room # Handle websocket Room

from io import BytesIO                          # Handle showing Raw Images
import datetime
import os

# Local Files and Fucntion
from modules import algorithm as alg
from modules import verify as verf
from modules import exception
from modules import utils
from modules import enc
from modules import db

import pyconf

conf = pyconf.read_ini("app.ini")



app = Flask(__name__)

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'sess:'
app.config['SESSION_REDIS'] = redis.from_url("redis://localhost:6379")
app.secret_key = conf["secret_key"]

# Create new advanced session
Session(app)

# Make webSocket server
Socket = SocketIO(app)

# Redis Cache System for chat
app.config['CHAT_KEY_PREFIX'] = 'chat:'
app.config['CHAT_REDIS'] = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Redis Cache for user status
app.config['USER_KEY_PREFIX'] = 'user:'
app.config['USER_REDIS'] = redis.Redis(host="localhost", port=6379, decode_responses=True)


# Make sessions Permenant
@app.before_request
def make_session_permanent():
    session.permanent = True

# Index
@app.route("/")
def index():
    userId = session["id"]
    return render_template("index.html", userId = userId)

# Login and signup
@app.route("/auth", methods=["POST","GET"])
def auth():
    # Check if user already Signed Up
    if session:
        return redirect(url_for("index"))
    
    # Check if user is signing Up
    if request.method == "POST" and "name" in request.form:
        # Get values from Form 
        name = request.form["name"]
        password = request.form["password"]
        email = request.form["email"]
        date = utils.timenow()
        
        # Check password Strength
        pwStatus, msg = utils.checkPass(password)
        if not pwStatus:
            return render_template("auth.html",msg = msg)
        
        # Register user
        regStatus, value = db.addUserInfo(name,password,email)

        # Check if registeration succeed
        if regStatus:
            msg = "Registeration Completed Successfully, Please Verify and Login with your account."
            
            # Send Verification Link
            verf.sendLink(email,f"https://siltna.dpdns.org/verify/{enc.encryptVerify(value)}")
            return render_template("auth.html",msg=msg)
        else:
            return render_template("auth.html",msg=value)
        
    # check if user is logging in
    if request.method == "POST" and "login" in request.form:
        # Get values from Form
        email = request.form["email"]
        password = request.form["password"]

        # Check if email Exists
        if not db.checkEmail(email):
            return render_template("auth.html",msg="There is no accounts associated with this Email")
        
        # Check if password matches and if verified
        if enc.checkpw(password,db.getUserInfo(None,email,useEmail=True)["password"]):
            # Check if user is verified
            if not db.checkVerified(db.getUserInfo(email=email,useEmail=True)["id"]):
                return render_template("auth.html",msg="Account is Not Verified, Please check Email or contact Support.")
            
            else:
                # create new session
                userInfo = db.getUserInfo(email=email,useEmail=True)
                privateKey = db.getPrivateKey(userId=userInfo["id"])
                
                session["loggedin"] = True
                session["id"] = userInfo["id"]
                session["name"] = userInfo["name"]
                session["privateKey"] = enc.decryptPrivateKey(privateKey,password)

                return redirect(url_for("index"))
        else:
            return render_template("auth.html",msg="The email or Password is incorrent")
    else:
        return render_template("auth.html")


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))



#####################################
#           USERS INFO              #
#####################################
#
# Handles User Profile, Images 
# And everything associated with him
# 
#####################################

@app.route("/u/<userId>")
def user(userId):
    # Check if user exists 
    if not db.checkId(userId):
        # Return 404 Error
        return abort(404)
    
    # Get user info from Database
    userInfo = db.getUserInfo(userId)

    # Get User informations
    date = userInfo["date"]
    date = date.strftime("%Y-%m-%d")

    # Get name and decrypt it
    name = userInfo["name"]
    name = enc.decrypt(name,date,"u")

    return render_template("userInfo.html",
                           name=name,
                           profilePic=f"<img src='/u/{userId}/icon'>")


# Handle User Icon
@app.route("/u/<userId>/icon")
def userIcon(userId):
    # Check if user exists 
    if not db.checkID(userId):
        # Return 404 Error
        return abort(404)
    
    # Get user Data from Database
    userData = db.getUserInfo(userId)

    date = userData["date"]
    icon = userData["profilePic"]

    # Check if there is user Icon
    if icon:
        if len(icon) > 0:
            # Decrypt user icon
            image = enc.decryptFile(icon,date)

            # Return Image data decrypted
            return send_file(BytesIO(image), mimetype="image/png")
        else:
            # If not return Empty Icon
            return send_file("static/images/emptyicon.png", mimetype="image/png")
    else:
        # If not return Empty Icon
        return send_file("static/images/emptyicon.png", mimetype="image/png")



#####################################
#           POSTS INFO              #
#####################################
#
# Handle Post Showing, Post Creation
# and anything Related to Posts
# 
#####################################

# Get Posts for Index
@app.route("/getPosts", methods=["GET"])
def getPosts():
    try:
        if not session.get("loggedin"):
            return jsonify({"status": "failed", "error": "You Must be Logged in"})

        userId = session["id"]
        posts = []
        post_ids = set()
        
        all_seen_post_ids = set()

        while len(posts) < 10:
            randomPosts = db.getRandomPosts(100)
            
            # If no posts are returned, we've exhausted the database
            if not randomPosts:
                break

            algPosts = alg.postArrange(randomPosts, userId)

            # Check if all posts returned by the algorithm have already been seen
            current_seen_count = 0
            for post in algPosts:
                if post["id"] in all_seen_post_ids:
                    current_seen_count += 1
            
            if len(algPosts) > 0 and current_seen_count == len(algPosts):
                break

            for post in algPosts:
                if post["id"] not in post_ids:
                    posts.append(post)
                    post_ids.add(post["id"])
                    
                all_seen_post_ids.add(post["id"]) # Add to the master list of seen posts

                if len(posts) >= 10:
                    break

        # Check if we found any posts at all before proceeding
        if not posts:
            return jsonify({"status": "success", "posts": []})

        decPosts = []
        for post in posts:
            postId = post["postId"]
            posterId = post["posterId"]
            date = post["date"]
            text = post["text"]
            images = post["images"]
            tags = post["tags"]

            imagesPath = []
            if "image" in tags:
                for i in range(len(images)):
                    imagesPath.append(f"<img src='/p/{postId}/i/{i}'>")

            if "text" in tags:
                text = enc.decrypt(text, date, "p")
            else:
                text = ""

            posterData = db.getUserInfo(posterId)
            if posterData:
                posterName = enc.decrypt(posterData["name"], posterData["date"])
                decPosts.append([[posterId, posterName], [text, imagesPath, str(date)]])
            else:
                continue 

        return jsonify({"status": "success", "posts": decPosts})

    except KeyError:
        return jsonify({"status": "failed", "error": "You Must be Logged in"})
    except Exception as e:
        print(f"Get POSTS error: {e}")
        return jsonify({"status": "failed", "error": str(e)})

# Getting Post info
@app.route("/p/<postId>",methods=["GET"])
def post(postId):
    # Check if method is "GET"
    if request.method == "GET":
        # Get post data
        status, postData = db.getPost(postId)

        # If getting post worked
        if status:
            # Get important data
            images = postData["images"]
            text   = postData["text"]
            tags   = postData["tags"]
            date   = postData["date"]

            # TODO: Get Detailed Data and add When Post is Posted
            # Example (an hour ago, date)

            date = date.strftime("%Y-%m-%d")

            # Check if post has images
            if "image" in tags:
                # Add image Path
                imagesPath = []
                for i in range(len(images)):
                    imagesPath.append(f"<img src='/p/{postId}/i/{i}")
            
            # Check if post has Text
            if "text" in tags:
                # Decrypt Text
                textDec = enc.decrypt(text,date,"p")
            else:
                textDec = ""

            # Return Post Values
            return render_template("post.html",images=imagesPath,text=textDec)
        else:
            # Return post.html with Error
            return render_template("post.html",msg=postData)
    else:
        # Give Forbidden Error
        abort(403)



# Post Images
@app.route("/p/<postId>/i/<i>",methods=["GET"])
def postImage(postId,i):
    if request.method == "GET":
        # Get Post Info
        status, postData = db.getPost(postId)

        # Check if succeed
        if status:
            # To prevent Index Errors 
            try:
                # Get images from Post
                images = postData["images"]
                date = postData["date"]

                # decrypt image
                imageData = enc.decryptFile(images[int(i)],date)

                return send_file(BytesIO(imageData), mimetype="image/png")
            except IndexError:
                # Send notfound Image
                send_file("static/images/notfound.png",mimetype="image/png")
        else:
            # Return not found Error
            print(f"Error Occured: {postData}")
            return send_file("static/images/notfound.png",mimetype="image/png")
    else:
        # Return Forbidden Error
        abort(403)


# Create Posts
@app.route("/createPost", methods=["POST"])
def createPost():
    # Check if request is to create Post and method is POST
    if request.method == "POST" and "createpost" in request.form:
        # Check if user is Logged in
        try:
            if not session["loggedin"]:
                return jsonify({"status": "failed","error": "You Must be Logged in"})
        except KeyError:
            return jsonify({"status": "failed","error": "You Must be Logged in"})
    
        # Post creation Handling
        try:
            # Get Text and Images from Request
            text = request.form["text"]
            files = request.files.getlist("file")

            # Handle acception of files
            fileList = []
            for i, singleFile in enumerate(files):
                # Check if file uploaded and allowed
                if singleFile and utils.allowed_file(singleFile):
                    # Check if it has secure name
                    fileName = secure_filename(singleFile.filename)

                    # Create new Path for the File
                    filePath = os.path.join('static/uploads',f"{i}_{session['id']}_{fileName}")

                    # Save file Locally
                    singleFile.save(filePath)

                    # Append path to total files
                    fileList.append(filePath)

            # Create Post
            creationStatus, Error = db.createPost(text,fileList,session['id'])

            # If error happened 
            if not creationStatus:
                return render_template("index.html",msg=str(Error))

        except Exception as e:
            raise e
        finally:
            # Remove all images uploaded
            for filePath in fileList:
                os.remove(filePath)
            
            return render_template("index.html",msg="Post Created")
    
    # If methods wasn't "POST"
    else:
        return redirect(url_for("/"))
    




"""
BASIC Statics
"""

@app.route("/static/icon.webp")
def staticicon():
    return send_file("static/images/icons/icon.webp",mimetype="image/webp")

@app.route("/static/fullicon.webp")
def staticfullicon():
    return send_file("static/images/icons/fullicon.webp",mimetype="image/webp")







#####################################
#           CHATS HANDLE            #
#####################################
@app.route("/c/<chatId>")
def chat(chatId):
    userId = session["id"]
    return render_template("chat.html",chatId=chatId,userId=userId)


# Check online status of user
@app.route("/c/u/<userId>/chechStatus")
def checkOnlineStatus(userId):
    # Get redis server
    redisServer = app.config["USER_REDIS"]

    # To prevent Unknown Errors
    try:
        # Get value from redis server
        value = redisServer.hgetall(f"{app.config["USER_KEY_PREFIX"]}{userId}")
        
        # Check if value empty
        if value:
            # Get status of user
            status = bool(value["status"])
            return status
        else:
            return False

    # Handle unknown Errors
    except Exception as e:
        print(f"[checkOnlineStatus] Unknown Status: {e}")
        return False


@app.route("/c/<chatId>/msgs")
def getMessages(chatId):
    # Get chat id from session
    userId = session["id"]

    # Check if chat Exitst
    chatInfo = db.getChatInfo(chatId)

    if chatInfo:
        # Get Redis Chat server
        redisServer = app.config["CHAT_REDIS"]

        chatCache = redisServer.hgetall(f"{app.config["CHAT_KEY_PREFIX"]}{chatId}")

        if chatCache:
            for i in chatCache["messages"]:
                chatInfo.append(i)
            return chatInfo
        else:
            return jsonify(chatInfo)
    else:
        return None
    




@Socket.on("joinChat")
def joinChat(data):
    # Get redis server
    chatRedis = app.config["CHAT_REDIS"]
    userRedis = app.config["USER_REDIS"]

    # Get userid from session
    userId = session["id"]
    chatId = data["chatid"]

    # set status of user in Cache
    userRedis.hset(f"{app.config["USER_KEY_PREFIX"]}{userId}", mapping={
        "userId": userId,
        "status": 1
    })

    # add Chat in Cache
    chatRedis.hset(f"{app.config["CHAT_KEY_PREFIX"]}{chatId}", mapping={
        "chatId": chatId,
        "messages": []
    })

    # make user join room
    join_room(chatId)



@Socket.on("leaveChat")
def joinChat(data):
    # Get redis server
    chatRedis = app.config["CHAT_REDIS"]
    userRedis = app.config["USER_REDIS"]

    # Get userid from session
    userId = session["id"]
    chatId = data["chatid"]

    # set status of user in Cache
    userRedis.hset(f"{app.config["USER_KEY_PREFIX"]}{userId}", mapping={
        "userId": userId,
        "status": 0
    })

    # delete Chat from Cache
    chatRedis.delete(f"{app.config["CHAT_KEY_PREFIX"]}{chatId}")

    # make user join room
    leave_room(chatId)



@Socket.on("send_message")
def sendMessage(data):
    # Get redis server
    chatRedis = app.config["CHAT_REDIS"]

    # Get needed Data
    chatId  = data["chatid"]
    message = data["message"]
    userId  = session["id"]
    dateSent = utils.timenow()
    dt = utils.timenow(ifDetailed=True)


    # Get other user public Key
    db.getChatInfo(chatId)
    
    # Create chat details
    messageInfo = {
        "senderId": userId,
        "message": message,
        "dateSend": dateSent,
        "detailedDate": dt
    }

    emit("recieve_message", messageInfo, room=chatId)
        


# Static js for chat
@app.route("/static/chat.js")
def chatjs():
    return send_file("/static/js/chat.js")






if __name__ == "__main__":
    # run app
    app.run(debug=True, host="0.0.0.0", port=5000)