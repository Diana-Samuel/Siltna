from PIL import Image

import string

_Extentions = ["png","jpg","jpeg","webp","gif","mp4"]



def checkPass(pw: str):
    if len(pw) < 8:
        return False, "Please make a password at least 8 letters long"
    if len(pw) >= 13:
        return False, "Please make a password between 8 and 13 characters long"

    check1 = check2 = check3 = check4 = False

    for i in pw:
        if i in string.ascii_lowercase:
            check1 = True
        elif i in string.ascii_uppercase:
            check2 = True
        elif i in string.digits:
            check3 = True
        elif i in string.punctuation:
            check4 = True

    if not check1:
        return False, "Password must have lowercase letters"
    if not check2:
        return False, "Password must have uppercase letters"
    if not check3:
        return False, "Password must have numbers"
    if not check4:
        return False, "Password must have symbols"

    return True, ""
    

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in _Extentions


def toWebp(filePath,savePath):
    Image.open(filePath).save(savePath, "webp", quality=80, lossless=False)
    return savePath
