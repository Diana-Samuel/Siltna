from flask import Flask, url_for, redirect      # Handle Functions and URL Works
from flask import request, jsonify, session     # Handle APIs and Requests
from flask import render_template, send_file    # For File Handling with Flask
from flask import abort                         # Error handling with flask
from werkzeug.utils import secure_filename      # Handle File uploads
from flask_session import Session               # Advanced Flask Session
import redis                                    # For Session handling

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
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
app.secret_key = conf["secret_key"]

# Create new advanced session
Session(app)

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
@app.route("/getPosts",methods=["GET"])
def getPosts():
    # Check if method is GET
    if request.method == "GET":
        # Check if user is Logged in
        try:
            if not session["loggedin"]:
                return jsonify({"status": "failed","error": "You Must be Logged in"})
        except KeyError:
            return jsonify({"status": "failed","error": "You Must be Logged in"})
        
        # Handle Getting posts
        try:
            # Get user ID from Session
            userId = session["id"]

            posts = []
            
            # Get Posts
            while True:
                # Get Random posts
                randomPosts = db.getRandomPosts(100)

                # Arrange Posts and Take best 2 scored
                algPosts = alg.postArrange(randomPosts,userId)

                # Get highest 2 Posts
                algPosts = algPosts[:2]

                # Add them to posts
                for post in algPosts:
                    for p in posts:
                        # check if posts is full (10 posts)
                        if len(posts) > 10:
                            break
                        else:
                            # Check if post is duplicated
                            if p["id"] != post["id"]:
                                posts.append(post)
                            else:
                                continue

                    # check if posts is full (10 posts)
                    if len(posts) > 10:
                        break

                # check if posts is full (10 posts)
                if len(posts) > 10:
                    break

            
            decPosts = []
            for post in posts:
                postId = post["postId"]
                posterId = post["posterId"]
                date = post["date"]
                text = post["text"]
                images = post["images"]
                tags = post["tags"]

                # check if post has images
                if "image" in tags:
                    # Put Image links
                    imagesPath = []

                    for i in range(len(images)):
                        imagesPath.append(f"<img src='/p/{postId}/i/{i}'>")

                # Check if post has Text
                if "text" in tags:
                    text = enc.decrypt(text,date,"p")
                else:
                    text = ""

                # Get Poster info
                posterData = db.getUserInfo(posterId)
                posterName = enc.decrypt(posterData["name"],posterData["date"])

                # Add to Post List
                decPosts.append([[posterId,posterName],[text,imagesPath,str(date)]])
            
            return jsonify({"status": "success", "posts": decPosts})
                    
        except KeyError as e:
            if e == "id":
                return jsonify({"status": "failed","error": "You Must be Logged in"})
            else:
                raise e
                return jsonify({"status":"failed","error": f"Key Error: {str(e)}"})
            
        except Exception as e:
            print(f"Get POSTS {e}")
            raise e
            return jsonify({"status":"failed","error": str(e)})


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



if __name__ == "__main__":
    # run app
    app.run(debug=True, host="0.0.0.0", port=5000)