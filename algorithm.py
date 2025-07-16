import db

import datetime

def postArrange(posts: list,userid: str) -> list:
    newPosts = {}
    for post in posts:
        score = 0
        postid = post["postId"]
        posterid = post["posterId"]
        text = post["text"]
        images = post["images"]
        status = post["status"]
        date = post["date"]
        tags = post["tags"]

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
