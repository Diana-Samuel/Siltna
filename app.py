from flask import Flask, render_template, send_from_directory, request
import time

import db
import enc

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("/index.html")

@app.route("/p/<userid>")
def user(userid):
    info = db.getinfo(enc.encuser(userid))

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
        
if __name__ == '__main__':
    app.run(debug=True,
            port=5000,
            host="0.0.0.0")