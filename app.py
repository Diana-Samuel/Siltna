from flask import Flask, render_template, request, jsonify, session, url_for, send_file, redirect
from werkzeug.utils import secure_filename

import os
import datetime
from io import BytesIO

import db
import enc
import algorithm as alg
import verify as verf
from utils import *
from exception import UploadError

import pyconf

s_conf = pyconf.read_ini("app.ini")

app = Flask(__name__)

app.secret_key = s_conf["secret_key"]




@app.route("/",methods=["POST","GET"])
def index():
    if request.method == "POST" and "createpost" in request.form:
        try:
            if session["loggedin"] == True:
                if ("file" not in request.files or request.files["file"].filename == "") and request.form["text"].strip() == "":
                    return url_for(index)
                try:
                    text = request.form["text"]
                    files = request.files.getlist("file")
                    fileList = []
                    for i,file in enumerate(files):
                        if file and allowed_file(file.filename):
                            filename = secure_filename(file.filename)
                            filepath = os.path.join('static/uploads',f"{i}_{session['id']}_{filename}")
                            file.save(filepath)
                            fileList.append(filepath)
                    status = db.createPost(text,fileList,session['id'])
                    if not status:
                        return render_template("index.html",msg="Upload did not success")
                except Exception as e:
                    raise e
                finally:
                    for i,file in enumerate(fileList):
                        os.remove(file)
                    return render_template("index.html",msg="Post created")
            else:
                return render_template("index.html",msg="Please log in before making a post")
        except KeyError:
            return render_template("index.html",msg="Please log in before making a post")
    else:
        return render_template("index.html")

@app.route("/getPosts",methods=["GET"])
def getposts():
    if request.method == "GET":
        try:
            if not session["loggedin"] == True:
                return jsonify({"status":"failed","error":"You Must be logged in"})
        except KeyError:
            return jsonify({"status":"failed","error":"You Must be logged in"})

        try:
            userid = session["id"]
            posts = alg.postArrange(db.getRandomPosts(),userid)
            decPosts = []
            for i in posts:
                post = []
                postid = i[0]
                posterid = i[1]
                date = i[-2]
                text = i[2]
                image = i[3]
                if len(image) > 0:
                    images = []
                    for i in range(len(image)):
                        images.append(f"<img src='/p/{postid}/i/{i}'>")
                if len(text) > 0:
                    text = enc.decrypt(text,date,'p')
                else:
                    text = ""
                post.append(text)
                post.append(images)
                post.append(str(date))
                posterdata = db.getuserinfo(posterid)
                postdate = posterdata[-2]
                postername = enc.decrypt(posterdata[1],postdate,'u')
                poster = [posterid,postername]
                decPosts.append([poster,post])
            return jsonify({"status":"success","posts": decPosts})
        except Exception as e:
            print(f"Get POSTS {e}")
            raise
            return jsonify({"status":"failed","error": str(e)})
        

@app.route("/auth", methods=["POST","GET"])
def auth():
    if session:
        return redirect(url_for("index"))    
    if request.method == "POST" and "name" in request.form:
        name = request.form["name"]
        pw = request.form["password"]
        email = request.form["email"]
        date = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
        pwStatus, msg = checkPass(pw)
        if not pwStatus:
            return render_template("auth.html",msg=msg)
        regStatus, userid = db.adduserinfo(name,pw,email)
        if regStatus:
            msg = "Registeration Completed Successfully"
            verf.sendLink(email,f"{enc.encryptVerify(db.getuserinfo(userid)[1])}")
            return render_template("auth.html",msg=msg)
        else:
            return render_template("auth.html",msg="Error registering")

    elif request.method == "POST" and "login" in request.form:
        email = request.form["email"]
        pw = request.form["password"]
        if not db.checkEmail(email):
            return render_template("auth.html",msg="There is no accounts associated with that email address")
        
        if enc.checkpw(pw,db.getuserinfo_byemail(email)[4]):
            if not db.checkVerified(db.getuserinfo_byemail(email=email)[0]):
                return render_template("auth.html",msg="You are not verified")            
            else:
                session['name'] = db.getuserinfo_byemail(email)[1]
                session['id'] = db.getuserinfo_byemail(email)[0]
                session['loggedin'] = True
                return redirect(url_for("index"))
        else:
            return render_template("auth.html",msg="The email or Password is incorrent") 
    else:
        return render_template("auth.html",msg="Opening the paeg")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/p/<postid>",methods=["POST","GET"])
def post(postid):
    if request.method == "GET":
        success, data = db.getPost(postid=postid)
        if success:
            image = data[3]
            text = data[2]
            date = data[-2]

            date = date.strftime("%Y-%m-%d")

            if len(image) > 0:
                images = []
                for i in range(len(image)):
                    images.append(f"<img src='/p/{postid}/i/{i}'>")
            if len(text) > 0:
                text = enc.decrypt(text,date,'p')
            else:
                text = ""
            return render_template("post.html",images=images,text=text)
        else:
            return render_template("post.html",msg="Failed")



@app.route("/p/<postid>/i/<i>")
def postImage(postid,i):
    success,data = db.getPost(postid)
    try:
        if success:
            image = data[3]
            date = data[-2]
            
            imageData = enc.decryptFile(image[int(i)],date=date)
            return send_file(BytesIO(imageData),mimetype="image/png")
        else:
            print(f"Error rendering image {data}")
            return send_file("static/images/notfound.png",mimetype="image/png")
    except IndexError:
        return send_file("static/images/notfound.png",mimetype="image/png")





@app.route("/u/<userid>",methods=["POST","GET"])
def user(userid):
    if request.method == "GET":
        if not db.checkID(userid):
            return render_template("error404.html")
        info = db.getuserinfo(userid)
        date = info[-2]
        date = date.strftime("%Y-%m-%d")
        name = enc.decrypt(info[1],date=date,encType="u")
        email = info[2]

        
        return render_template("userinfo.html",info=f"<div><h1>Name: {name}</h1><p>Email: {email}</p></div>")
    elif request.method == "POST":
        try:
            if not db.checkID(userid):
                return jsonify({"status": "Failed","Error": "404"})
            info = db.getuserinfo(userid)
            date = info[-2]
            date = date.strftime("%Y-%m-%d")
            name = enc.decrypt(info[1],date=date,encType="u")
            email = info[2]
            phone = info[3]
            if phone != None:
                phone = enc.decrypt(info[3],date=date,encType="u")
            return jsonify({"status":"success","name": name,"email": email,"phone": phone})
        except Exception as e:
            return jsonify({"status": "Failed","Error": str(e)})


@app.route("/u/<userid>/icon/")
def usericon(userid):
    data = db.getuserinfo(userid)
    date = data[-2]
    icon = data[-3]
    if len(icon) > 0:
        imageData = enc.decryptFile(icon,date)
    else:
        return send_file("static/images/emptyicon.png", mimetype="image/png")
    return send_file(BytesIO(imageData),mimetype="image/png")



@app.route("/verify/<userid>")
def verify(userid):
    userid = enc.decryptVerify(userid)
    if not db.checkID(userid):
        msg = "cannot find the user. Please check your Email for the link"

    return render_template("verify.html",msg=msg)




"""
Statics
"""

@app.route("/static/icon.webp")
def staticicon():
    return send_file("static/images/icons/icon.webp",mimetype="image/webp")

@app.route("/static/fullicon.webp")
def staticfullicon():
    return send_file("static/images/icons/fullicon.webp",mimetype="image/webp")







if __name__ == '__main__':
    app.run(debug=True,
            port=5000,
            host="0.0.0.0")
    
