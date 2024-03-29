# Team mapp - Pratham Rawat, Junhee Lee, Kelvin Ng & David Xiedeng
# SoftDev1 pd1
# P#00 - Da Art of Storytellin'
# 2019-10-28

from flask import Flask, render_template, session, flash, request, redirect
import sqlite3, os
import datetime

app = Flask(__name__)

db = sqlite3.connect("mapp_site.db") #open if file exists, otherwise create
c = db.cursor()

app.secret_key = os.urandom(32)

#b# ========================================================================
#b# Site Interaction

@app.route("/")
def loggingIn():
    if 'username' in session:
        print("username in session")
        flash("Hello " + session['username'] + "!")
        return render_template('homepage.html') #user is redirected to the response page if logged in
    print("username not in session, redirecting to login")
    return redirect('/login') #returns to login page if user is not logged in

@app.route("/login", methods=['GET', "POST"])
def login():
    loginCode = ""
    try:
        loginCode = loginAccount(request.form["username"], request.form["password"]) #checks if username exists in database and that the password matches it
    except:
        print("yeet")
    flash(loginCode)
    if loginCode == "Successful login":
        return redirect('/') #redirects to homepage if successful login
    return render_template('login.html') #returns to login page if user is not logged in

@app.route("/logout")
def loggingOut():
    if 'username' not in session:
        return redirect('/login') #redirects to login page if not in session
    session.pop('username') #removes session when logging out
    flash("You have successfully logged out!")
    return redirect("/") #redircts to homepage page if logged in and in session

@app.route("/create", methods=['GET', 'POST'])
def signUp():
    signUpCode = ""
    try:
        signUpCode = createAccount(request.form["username"], request.form["password"], request.form["password2"]) #adds new account info to database
    except:
        print("yeet")
    flash(signUpCode)
    return render_template("createAccount.html") #redirects to createAccount page

@app.route("/createStory", methods=['GET', 'POST'])
def newStory():
    if 'username' not in session:
        return redirect('/login') #if not in sesssion, redirects to login page (if user happens to stumble upon this page without logging in)
    createStoryCode = ""
    if request.method == 'POST':
        Title, Story = request.form['title'].replace("\'", ""), request.form['introduction'] #takes user input
        for char in "!*'();:@&=+$,/?%#[]":
            Title = Title.replace(char, "") #replaces "!*'();:@&=+$,/?%#[]" characters with nothing in order to avoid bugs/errors
        createStoryCode = uploadStory(Title.replace("\'", ""), Story.replace("\'", ""))
        flash(createStoryCode)
        if createStoryCode != "Story uploaded":
            return render_template("createStory.html", ttle = Title, Story = Story) #if error occurs, it keeps user input in text box
        else:
            buildTable(Title, {"update": "TEXT", "user" : "TEXT UNIQUE", "time": "TIMESTAMP"})
            addRow(Title, (Story.replace("\'", ""), session['username'], datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))) #adds story, time, author (username) to database
            return render_template("homepage.html") #returns back to homepage after successful creation of story
    else:
        return render_template("createStory.html", ttle = "", Story = "") #if 1st time on this page, return empty text field awaiting for user input

@app.route("/viewStory")
def viewStories():
    if 'username' not in session:
        return redirect('/login') #if not in sesssion, redirects to login page (if user happens to stumble upon this page without logging in)
    db = sqlite3.connect("mapp_site.db")
    c = db.cursor()
    c.execute("SELECT * FROM stories")
    fetch = c.fetchall()
    print(fetch)
    return render_template("allStories.html", stories = fetch) #redirects to allStories which displays all existing stories in database

@app.route("/editStory", methods=['GET', 'POST'])
def editStory():
    if 'username' not in session:
        return redirect('/login')
    if request.method == "GET":
        arg1 = list(dict(request.args).keys())[0]
        arg2 = request.args[arg1]
        #c# (title, author)
        info = [arg1, arg2]
        db = sqlite3.connect("mapp_site.db")
        c = db.cursor()
        c.execute("SELECT story FROM stories WHERE title = \'{}\' AND author = \'{}\'".format(info[0],info[1]))
        fetched = c.fetchall()
        db.close()
        return render_template("updateStory.html", ttle = info[0], Story = fetched[0][0]) #redirects to page that allows user to update an existing story

@app.route("/mystories")
def myStories():
    if 'username' not in session:
        return redirect('/login')
    allstories=command("SELECT title FROM stories")
    mystories=[]
    for story in allstories:
        authors = command("SELECT user FROM '{}'".format(story[0]))
        authors = map(lambda x: x[0], authors)
        if session['username'] in authors:
            mystories.append(command("SELECT * FROM stories WHERE title = '{}'".format(story[0]))) #selects stories created by the account with that username
    mystories=map(lambda x:x[0], mystories)
    return render_template("myStories.html", stories=mystories) #redirects to myStories listing out all stories made by this user

@app.route("/addToStory", methods=['GET', 'POST'])
def addToStory():
    if 'username' not in session:
        return redirect('/login')
    title = request.args['title'].replace("\'", "")
    addRow(title , [request.form['introduction'].replace("\'", ""), session['username'],  datetime.datetime.now().strftime('%Y-%m-%d %H:%M')]) #adds update to story, the username, and date to database
    command("UPDATE stories SET story='{}';".format(request.form['introduction'].replace("\'", ""))) #updates story
    return redirect("/readStory?title={}".format(title)); #redirects to page that allows user to read all updates to story

@app.route("/readStory")
def readStory():
    if 'username' not in session:
        return redirect('/login')
    try:
        storyTitle = request.args['title'] #checks if story exists
    except:
        flash("Story does not exist!")
        return render_template("homepage.html") #returns to homepage if not
    print(storyTitle)
    print(command("SELECT \"user\" FROM '{}' WHERE  \"user\" = \"{}\";".format(storyTitle, session['username'])))
    if(command("SELECT \"user\" FROM '{}' WHERE  \"user\" = \"{}\";".format(storyTitle, session['username'])) == []):
        author = command("SELECT author FROM stories WHERE title = \"{}\";".format(storyTitle))[0][0]
        return redirect("/editStory?{}={}".format(storyTitle, author))
    else:
        story = command("SELECT \"update\", \"user\", \"time\" FROM '{}' ORDER BY \"time\";".format(storyTitle))
        return render_template("readStory.html", title = storyTitle, stories = story)

#b# Site Interaction
#b# ========================================================================
#b# Database Interaction

#d# calls c.execute(command)
def command(command):
    db = sqlite3.connect("mapp_site.db") #open if file exists, otherwise create
    c = db.cursor()
    print(command)
    c.execute(command)
    output = c.fetchall()
    db.commit()
    db.close()
    return output

#d# create table and remove table if exists
#d# takes in a filename and the key(dict)
def buildTable(name, kc):
    toBuild = "CREATE TABLE if not exists \"" + name + "\"("
    for el in kc:
        toBuild = toBuild + "\"{}\" {}, ".format(el, kc[el])
    toBuild = toBuild[:-2] + ")"
    command(toBuild)

#d# adds data to table, whole row insertion
#d# takes string table, and list val
def addRow(table, val):
    toDo = "INSERT INTO \"{}\" VALUES (".format(table)
    for el in val:
        if type(el) == int:
            toDo = toDo + str(el) + ", "
        else:
            toDo = toDo + "\'" + el + "\'" + ", "
    toDo = toDo[:-2] + ")"
    command(toDo)

#b# Database Interaction
#b# ========================================================================
#b# Accounts Table Code

buildTable("accounts", {"username": "TEXT", "password": "TEXT"})
buildTable("stories", {"title": "TEXT", "author": "TEXT", "time": "TEXT", "story": "TEXT"})

#d# takes in three strings and reads from table accounts if data exists
#d# creates account if suitable input is provided
#d# returns String message
def createAccount(username, password, passwdverf):
    db = sqlite3.connect("mapp_site.db")
    c = db.cursor()
    c.execute("SELECT username FROM accounts WHERE username = \'{}\'".format(username))
    fetched = c.fetchall()
    db.close()
    if len(username) < 1:
        return "username too short"
    elif "'" in username:
        return "Please do not include ' in the username"
    elif len(password) < 1:
        return "password too short"
    elif len(fetched) > 0:
        return "username exists"
    elif password != passwdverf:
        return "password does not match"
    else:
        addRow("accounts", (username, password))
        return "account created"

def loginAccount(username, password):
    db = sqlite3.connect("mapp_site.db")
    c = db.cursor()
    cmd = "SELECT username, password FROM accounts WHERE username = '{}';".format(username)
    c.execute(cmd)
    fetched = c.fetchall()
    print(fetched)
    db.close()
    if len(fetched) < 1:
        return "username does not exist"
    elif fetched[0][1] != password:
        return "password is incorrect"
    else:
        session['username'] = username  #starts a session if user inputs correct existing username and password
        print('created session')
        return "Successful login"

#d# pushes story inputs to database
#d# rejects upload if:
#d# - title is empty
#d# - story is empty
#d# - title already exists
def uploadStory(title, story):
    db = sqlite3.connect("mapp_site.db")
    c = db.cursor()
    c.execute("SELECT title FROM stories WHERE title = \'{}\'".format(title))
    fetched = c.fetchall()
    db.close()
    #c# title already exists
    if len(fetched) > 0:
        return "Title already exists."
    #c# title is empty
    elif len(title) < 1:
        return "Please title your story"
    #c# story is empty
    elif len(story) < 1:
        return "Please write a story"
    else:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        addRow("stories", (title, session['username'], timestamp, story))
        return "Story uploaded"

#d# takes two string inputs returns list of details
#d# returns list of strings
def readStory(title, story):
    db = sqlite3.connect("mapp_site.db")
    c = db.cursor()
    c.execute("SELECT title, story FROM stories WHERE title = \'{}\' AND story = \'{}\'".format(title, story))
    fetched = c.fetchall()
    db.close()
    return fetched

#d# takes 4 strings, returns string error message
#d# changes tables to add newAuthor, and updatedStory
def updateStory(title, author, newAuthor, updateToStory):
	db = sqlite3.connect("mapp_site.db")
	c = db.cursor()
	#c# retrieve author and story
	c.execute("SELECT story FROM stories WHERE title = \'{}\' AND author = \'{}\'".format(title, author))
	fetched = c.fetchall()
	#c# update authors, and story text
	authors = author 
	if "and" in fetched[1]:
		andIndex = author.index(" and")
		authors = author[:andIndex] + author[andIndex + 4:]
	authors = authors + ", and" + newAuthor
	newStory = fetched[3] + "\n" + updateToStory
	c.execute("UPDATE stories SET author = \'{}\', story = \'{}\' WHERE title = \'{}\', and author = \'{}\'".format(authors, newStory, title, author))
	db.commit()
	db.close()
	return

#b# Accounts Table Code
#b# ========================================================================

db.close()  #close database
#c# Bottom of DB Code

if __name__ == "__main__":
	app.debug = True
	app.run()
