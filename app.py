from flask import Flask, render_template, send_from_directory, request, jsonify
import time

import db
import enc

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("/index.html")

@app.route("/register", methods=["POST","GET"])
def register():
    if request.method == "POST" and "name" in request.form:
        name = request.form["name"]
        pw = request.form["password"]
        email = request.form["email"]
        if db.adduserinfo(name,pw,email):
            msg = "Registeration Completed Successfully"
            return render_template("register.html",msg=msg)
        else:
            return render_template("register.html",msg="Error registering")
    else:
        return render_template("register.html",msg="")
        
@app.route("/p/<postid>",methods=["POST","GET"])
def post(postid):
    if request.method == "GET":
        print()

@app.route("/u/<userid>",methods=["POST","GET"])
def user(userid):
    if request.method == "GET":
        if not db.checkID(userid):
            return render_template("error404.html")
        info = db.getuserinfo(userid)
        date = info[-1]
        date = date.strftime("%Y-%m-%d")
        name = enc.decrypt(info[1],date=date,encType="u")
        email = enc.decrypt(info[2],date=date,encType="u")

        
        return render_template("userinfo.html",info=f"<div><h1>Name: {name}</h1><p>Email: {email}</p></div>")
    elif request.method == "POST":
        try:
            if not db.checkID(userid):
                return jsonify({"status": "Failed","Error": "404"})
            info = db.getuserinfo(userid)
            date = info[-1]
            date = date.strftime("%Y-%m-%d")
            name = enc.decrypt(info[1],date=date,encType="u")
            email = enc.decrypt(info[2],date=date,encType="u")
            phone = info[3]
            if phone != None:
                phone = enc.decrypt(info[3],date=date,encType="u")
            return jsonify({"status":"success","name": name,"email": email,"phone": phone})
        except Exception as e:
            return jsonify({"status": "Failed","Error": str(e)})

    
@app.route("/verify/<userid>")
def verify(userid):
    userid = enc.decryptVerify(userid)
    if not db.checkID(userid):
        msg = "cannot find the user. Please check your Email for the link"


    return render_template("verify.html",msg=msg)
if __name__ == '__main__':
    app.run(debug=True,
            port=5000,
            host="0.0.0.0")