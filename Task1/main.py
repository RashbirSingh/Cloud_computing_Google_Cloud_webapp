from datetime import datetime
from flask import Flask, render_template
from flask import request, session
from google.cloud import datastore, storage

import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="static/s3810585assignment1task1-9ddd41bfb517.json"

datastore_client = datastore.Client()

app = Flask(__name__)
app.secret_key = "hello"

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)


def download_blob(bucket_name, source_blob_name, destination_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_blob_name)


@app.route('/')
def root():
    if 'CurrentActiveUser' in session:
        return render_template('index.html',
                               userlog = "logout",
                               userlogimage = "log-out",
                               userlogtext = " Logout")
    else:
        return render_template('index.html',
                               userlog="login",
                               userlogimage="log-in",
                               userlogtext=" Login")

@app.route('/forum')
def forum():
    if 'CurrentActiveUser' in session:
        kindUserImg = "User"
        id = session["CurrentActiveUser"]
        postquery = datastore_client.query(kind="postbox")
        postquerylist = list(postquery.fetch(limit=10))
        keyImg = datastore_client.key(kindUserImg, id)
        taskImg = datastore_client.get(keyImg)

        download_blob(taskImg["bucketname"],
                      taskImg["userimage"],
                      "static/userimage/" + taskImg["userimage"])
        return render_template('forum.html', user_name=session["CurrentActiveUserName"],
                               userImageURL="static/userimage/" + taskImg["userimage"],
                               postquerylist=postquerylist
                               )
    else:
        return render_template('notification.html',
                               notification="Please Login to Access this Page",
                               userlog="login",
                               userlogimage="log-in",
                               userlogtext=" Login"
                               )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        kindUserInfo = "Task"
        kindUserImg = "User"
        req = request.form
        id = req.get("id")
        password = req.get("password")
        key = datastore_client.key(kindUserInfo, id)
        task = datastore_client.get(key)

        if (task is not None) and (password == task["password"]):
            session["CurrentActiveUser"] = id
            session["CurrentActiveUserName"] = task['user_name']

            # RETURN FORM
            keyImg = datastore_client.key(kindUserImg, id)
            taskImg = datastore_client.get(keyImg)

            download_blob(taskImg["bucketname"],
                          taskImg["userimage"],
                          "static/userimage/"+taskImg["userimage"])

            ##GETTING POST DATA
            postquery = datastore_client.query(kind="postbox")
            postquerylist = list(postquery.fetch(limit=10))

            for postimageeach in postquerylist:
                download_blob("s3810585-storage-task1",
                              postimageeach["img"],
                              "static/postimage/" + postimageeach["img"])

            return render_template('forum.html', user_name = session["CurrentActiveUserName"],
                                   userImageURL = "static/userimage/"+taskImg["userimage"],
                                   postquerylist=postquerylist
                                   )
        else:
            return render_template('notification.html',
                                   notification = "ID or Password is Invalid",
                                   userlog="login",
                                   userlogimage="log-in",
                                   userlogtext=" Login"
                                   )

    else:
        return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":

        kindUserInfo = "Task"
        kindUserImg = "User"
        req = request.form

        #Getting Form data
        id = req.get("id")
        password = req.get("password")
        user_name = req.get("user_name")
        img = request.files['file']
        img.save(img.filename)

        #Getting datastore client entity for user info
        key = datastore_client.key(kindUserInfo, id)
        getterTask = datastore_client.get(key)

        #Getting datastore client entity for user image
        keyImg = datastore_client.key(kindUserImg, id)
        userImg = datastore.Entity(key=keyImg)

        if getterTask is None:
            task = datastore.Entity(key=key)
            query = datastore_client.query(kind="Task")
            query.add_filter("user_name", "=", user_name)
            if len(list(query.fetch())) > 0:
                return render_template('notification.html',
                                       notification="The Username Already Exists",
                                       userlog="login",
                                       userlogimage="log-in",
                                       userlogtext=" Login"
                                       )
            else:
                #Updaing entity
                task["user_name"] = user_name
                task["password"] = password
                datastore_client.put(task)

                userImg["bucketname"] = "s3810585-storage-task1"
                userImg["userimage"] = img.filename
                datastore_client.put(userImg)

                upload_blob("s3810585-storage-task1", img.filename, img.filename)
                os.remove(img.filename)

                return render_template('login.html')
        else:
            return render_template('notification.html',
                                   notification="The ID Already Exists",
                                   userlog="login",
                                   userlogimage="log-in",
                                   userlogtext=" Login"
                                   )

    if 'CurrentActiveUser' in session:
        return render_template('register.html',
                               userlog = "logout",
                               userlogimage = "log-out",
                               userlogtext = " Logout")
    else:
        return render_template('register.html',
                               userlog="login",
                               userlogimage="log-in",
                               userlogtext=" Login")

@app.route('/userpage', methods=['GET', 'POST'])
def userpage():
    postquery = datastore_client.query(kind="postbox")
    id = session["CurrentActiveUser"]
    postquery.add_filter("id", "=", id)
    postquerylist = list(postquery.fetch())
    return render_template('userpage.html',
                           postquerylist = postquerylist)


@app.route('/editpost', methods=['GET', 'POST'])
def editpost():
    if request.method == "POST":
        kindUserInfo = "Task"
        kindUserImg = "User"
        req = request.form
        postid = req.get("postid")
        postChangeKey = datastore_client.key('postbox',int(postid))
        postChangeTask = datastore_client.get(postChangeKey)
        return render_template("editpost.html", postChangeTask=postChangeTask)

        # postChangeKey = datastore_client.key('postbox',postid )
        # postChangeTask = datastore_client.get(postChangeKey)
        # postChangeTask["id"] = id
        # postChangeTask["subject"] = subject
        # postChangeTask["msg"] = msg
        # postChangeTask["user_names"] = session["CurrentActiveUser"]
        # postChangeTask["datetime"] = datetime.now()
        # postChangeTask["userImage"] = taskImg["userimage"]
        # postChangeTask["img"] = img.filename

    postquery = datastore_client.query(kind="postbox")
    id = session["CurrentActiveUser"]
    postquery.add_filter("id", "=", id)
    postquerylist = list(postquery.fetch())
    return render_template('userpage.html',
                           postquerylist = postquerylist)


@app.route('/pushchange', methods=['GET', 'POST'])
def pushchange():
    if request.method == "POST":
        kindUserImg = "User"
        req = request.form
        postid = req.get("postid")
        subject = req.get("subject")
        msg = req.get("msg")
        img = request.files['file']
        img.save(img.filename)
        upload_blob("s3810585-storage-task1", img.filename, img.filename)

        postChangeKey = datastore_client.key('postbox', int(postid))
        postChangeTask = datastore_client.get(postChangeKey)
        postChangeTask["subject"] = subject
        postChangeTask["msg"] = msg
        postChangeTask["img"] = img.filename
        datastore_client.put(postChangeTask)

        postquery = datastore_client.query(kind="postbox")
        id = session["CurrentActiveUser"]
        postquery.add_filter("id", "=", id)
        postquerylist = list(postquery.fetch())


        download_blob("s3810585-storage-task1",
                      postChangeTask["img"],
                      "static/postimage/" + postChangeTask["img"])

        return render_template('userpage.html',
                               postquerylist=postquerylist)

@app.route('/changepass', methods=['GET', 'POST'])
def changepass():
    if request.method == "POST":
        kindUserInfo = "Task"
        kindUserImg = "User"
        id = session["CurrentActiveUser"]
        req = request.form
        oldPassword = req.get("oldpass")
        newPassword = req.get("newpass")

        changeKey = datastore_client.key(kindUserInfo,id )
        changeTask = datastore_client.get(changeKey)

        if changeTask["password"] == oldPassword:
            changeTask["password"] = newPassword
            datastore_client.put(changeTask)
            return render_template('userpage.html')
        else:

            return render_template('notification.html',
                                   notification="The Old Password is Incorrect",
                                   userlog="logout",
                                   userlogimage="log-in",
                                   userlogtext=" Logout"
                                   )


@app.route('/postarea', methods=['GET', 'POST'])
def postarea():
    if request.method == "POST":
        kindPostBox = "postbox"
        kindUserImg = "User"
        req = request.form
        subject = req.get("subject")
        msg = req.get("msg")
        img = request.files['file']
        img.save(img.filename)
        upload_blob("s3810585-storage-task1", img.filename, img.filename)
        id = session["CurrentActiveUser"]

        keyImg = datastore_client.key(kindUserImg, id)
        taskImg = datastore_client.get(keyImg)
        download_blob(taskImg["bucketname"],
                      taskImg["userimage"],
                      "static/userimage/"+taskImg["userimage"])

        keyPostBox = datastore_client.key(kindPostBox)
        taskPostBox = datastore.Entity(key=keyPostBox)
        taskPostBox["id"] = id
        taskPostBox["subject"] = subject
        taskPostBox["msg"] = msg
        taskPostBox["user_names"] = session["CurrentActiveUser"]
        taskPostBox["datetime"] = datetime.now()
        taskPostBox["userImage"] = taskImg["userimage"]
        taskPostBox["img"] = img.filename

        datastore_client.put(taskPostBox)

        ##GETTING POST DATA
        postquery = datastore_client.query(kind="postbox")
        postquerylist = list(postquery.fetch(limit=10))

        for postimageeach in postquerylist:
            download_blob("s3810585-storage-task1",
                          postimageeach["img"],
                          "static/postimage/"+postimageeach["img"])

        return render_template('forum.html',
                               user_name=session["CurrentActiveUserName"],
                               userImageURL="static/userimage/" + taskImg["userimage"],
                               postquerylist=postquerylist)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop("CurrentActiveUser", None)
    session.pop("CurrentActiveUserName", None)
    return render_template('login.html')


if __name__ == '__main__':

    app.run(host='127.0.0.1', port=8080, debug=True)


kind = "Task"
name = "s38105859"
task_key = datastore_client.key(kind, name)
task = datastore.Entity(key=task_key)
task["user_name"] = "rashbir kohli9"
task["password"] = "901234"
datastore_client.put(task)