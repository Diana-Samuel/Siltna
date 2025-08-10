import smtplib
from email.message import EmailMessage

from modules.db import checkVerified, checkID

import pyconf

emailConf = pyconf.read_ini("email.ini")



def sendLink(email: str, link: str):
    try:
        msg = EmailMessage()
        msg["Subject"] = "Verify your email in Siltna."
        msg["From"] = emailConf["login"]
        msg["To"] = email
        msg.set_content(f"""{link}""",subtype='html')
        with smtplib.SMTP_SSL(emailConf["smtp_server"], int(emailConf["port"])) as smtp:
            smtp.login(emailConf["login"], emailConf["password"])
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Error Sending link: {e}")
        return False
    

def verifyUser(userid: str):
    try:
        if not checkID(userid):
            return False
        checkVerified(userid)

    except Exception as e:
        print(f"Error verifying User With id {userid}: {e}")
        return False