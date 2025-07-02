import db

import datetime

def postArrange(posts: list,userid: str) -> list:
    newPosts = {}
    for post in posts:
        score = 0
        postid = post[0]
        posterid = post[1]
        text = post[2]
        images = post[3]
        status = post[-3]
        date = post[-2]
        tags = post[-1]
        interests = db.getInterests(userid)
        if not status:
            continue
        userInfo = db.getuserinfo(userid)
        following = userInfo[-1]
        if posterid in following:
            score += 50
        if "text" in interests and len(text) > 0:
            score += 10
        if "image" in interests and len(images) > 0:
            score += 10
        timenow = datetime.datetime.now(datetime.UTC)
        diffInDays = (timenow.date() - date).days
        score -= diffInDays * 2
        newPosts[postid] = score
    newPosts = sorted(newPosts)
    newnewPosts = []
    for i in newPosts:
        newnewPosts.append(db.getPost(i)[1])
    return newnewPosts
