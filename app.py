from flask import Flask, render_template, send_from_directory, request, jsonify, session, url_for
import time
import string

import db
import enc
import verify as verf

import pyconf

s_conf = pyconf.read_ini("app.ini")

app = Flask(__name__)

app.secret_key = s_conf["secret_key"]


    

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/auth", methods=["POST","GET"])
def register():
    if request.method == "POST" and "name" in request.form:
        name = request.form["name"]
        pw = request.form["password"]
        email = request.form["email"]
        pwStatus, msg = checkPass
        if not pwStatus:
            return render_template("auth.html",msg=msg)
        if db.adduserinfo(name,pw,email):
            msg = "Registeration Completed Successfully"
            verf.sendLink(email,f"{enc.encryptVerify(db.getuserinfo_byemail(email)[1])}")
            return render_template("auth.html",msg=msg)
        else:
            return render_template("auth.html",msg="Error registering")
        


    elif request.method == "POST" and "login" in request.form:
        email = request.form["email"]
        pw = request.form["password"]
        if not db.checkEmail(email):
            return render_template("auth.html",msg="There is no accounts associated with that email address")
        if enc.checkpw(pw,db.getuserinfo_byemail(email)[3]):
            if not db.checkVerified(db.getuserinfo_byemail(email=email)[0]):
                return render_template("auth.html",msg="")
            else:
                session['name'] = db.getuserinfo_byemail(email)[1]
                session['id'] = db.getuserinfo_byemail(email)[0]
                return url_for(index)

    else:
        return render_template("auth.html",msg="")


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
    




def checkPass(pw: str):
    msg = ""
    if len(pw) < 8:
        msg = "Please make a password at least 8 letters long"
        return msg,False
    if len(pw) >= 13:
        msg = "Please make a password between 8 and 13 characters long"
        return msg,False
    check1 = False          # lowercase
    check2 = False          # Uppercase
    check3 = False          # Number
    check4 = False          # Symbol
    for i in pw:
        if i in string.ascii_lowercase:
            check1 = True
            continue
        if i in string.ascii_uppercase:
            check2 = True
            continue
        if i in string.digits:
            check3 = True
            continue
        if i in string.punctuation:
            check4 = True
            continue
        
        if check1 and check2 and check3 and check4:
            return True, ""
    
    if not check1:
        msg = "Password must Have lowercase letters"
        return False, msg
    if not check2:
        msg = "Password must Have uppercase letters"
        return False, msg
    if not check3:
        msg = "Password must Have Numbers"
        return False, msg
    if not check4:
        msg = "Password must Have Symbols"
        return False, msg
    