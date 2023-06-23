from flask import Flask
from flask import render_template
from flask import url_for
from flask import redirect
from flask import request
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from flask import session
from flask import flash


app = Flask(__name__)
app.secret_key = "Secret"
app.permanent_session_lifetime = timedelta(minutes=5)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users_db.sqlite3'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///api_db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Users(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(100))
    surname = db.Column("surname", db.String(100))
    mail = db.Column("mail", db.String(100))
    password = db.Column("password", db.String(100))

    def __str__(self):
        return "name:{} \n surname: {} \n mail: {} \n password: {}".format(self.name, 
                self.surname, self.mail, self.password)
    

class Api(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(100))
    img_link = db.Column("img_link", db.String(200))
    img_num = db.Column("num", db.Integer)
    def __str__(self):
        return "{}{}{}".f(self.name, self.img_link, self.img_num)
    

with app.app_context():
    db.create_all()
    
   
@app.route("/")
@app.route("/home")
def home_page():
    return render_template('home.html')


@app.route('/main', methods=["POST", "GET"])
def main_page():
   if "email" not in session and "name" not in session and "password" not in session and "surname" not in session:
    return redirect(url_for('login_page'))
   if request.method == "POST":
        import requests
        import json
        url = "https://api.imgflip.com/get_memes"
        resp = requests.get(url).text
        resp_dict= json.loads(resp)
        list = []
        index = request.form["number"]
        list.append(resp_dict["data"]["memes"][int(index)]["name"])
        list.append(resp_dict["data"]["memes"][int(index)]["url"])
        api = Api(name = list[0], img_link = list[1], img_num=index)
        db.session.add(api)
        db.session.commit()
        query1 = Api.query.with_entities(Api.name).filter_by(img_num=index).first()
        query2 = Api.query.with_entities(Api.img_link).filter_by(img_num=index).first()
        with open('static\meme.png', 'wb') as file:
         file.write(requests.get(query2[0]).content)
         file.close()
        flash(query1[0])
        return render_template('main_page.html')
   else:
    return render_template('main_page.html')
   
   
@app.route("/login", methods=["POST", "GET"])
def login_page():
    if "email" in session and "name" in session and "password" in session and "surname" in session:
      return (redirect(url_for("user")))
    if request.method == "POST":
       with app.app_context():
        mail = request.form["email"]
        password = request.form["password"]
        query1 = Users.query.with_entities(Users.mail).filter_by(mail=mail).all()
        query2 = Users.query.with_entities(Users.password).filter_by(password=password).all()
        query3 = Users.query.with_entities(Users.name).filter_by(password=password).all()
        query4 = Users.query.with_entities(Users.surname).filter_by(password=password).all()
        if query1 and query2 and query3 and query4:
            db_mail = query1[0][0]
            db_password = query2[0][0]
            db_name = query3[0][0]
            db_surname = query4[0][0]
            if mail == db_mail and password == db_password:
                session["email"]  = db_mail
                session["password"] = db_password
                session["name"] = db_name
                session["surname"] = db_surname
                return(redirect(url_for("user")))
        else:
            flash("Incorrect mail or password")
            return(redirect(url_for("login_page")))
    else:
       return(render_template("login.html"))
     
       
@app.route("/sign_up", methods=["POST", "GET"])
def sign_up():
    if "email" in session and "name" in session and "password" in session and "surname" in session:
      return (redirect(url_for("user")))
    if request.method == "POST":
        name = request.form["name"]
        surname = request.form["surname"]
        mail = request.form["email"]
        password = request.form["password"] 
        numbers = "1234567890"
        query_mail = Users.query.with_entities(Users.mail).filter_by(mail=mail).all()
        for i in name:
         if i in numbers:
            flash("Invalid name with number in it!", "info") 
            return render_template('sign_up_page.html')
        for i in surname:
         if i in numbers:
            flash("Invalid surname with number in it!", "info") 
            return render_template('sign_up_page.html')
        if len(name) < 2:
         flash("Invalid name more than 1 charachters!", "info") 
         return render_template('sign_up_page.html')
        elif len(surname) <= 5:
         flash("Invalid surname more than 4 charachters!", "info") 
         return render_template('sign_up_page.html') 
        elif  '@' and '.' not in mail:
          flash("Invalid mail")
          return render_template('sign_up_page.html')
        elif query_mail:
          flash("mail already used")
          return render_template('sign_up_page.html')
        elif len(password) <= 10:
         flash("Invalid password more than 9 charachters!", "info") 
         return render_template('sign_up_page.html') 
        else:
           session["email"] = mail
           session["name"] = name
           session["surname"] = surname
           session["password"] = password
           db.session.add(Users(name=name, surname=surname, mail=mail, password=password))
           db.session.commit()
           return redirect(url_for("user"))

    else:
        return render_template('sign_up_page.html')    


@app.route("/user")
def user():
    if "name" in session and "surname" in session and "email" in session and "password" in session:
        name = session["name"]
        surname = session["surname"]
        mail = session["email"]
        password = session["password"]
        return render_template('user.html', name=name, surname=surname, mail=mail, password=password)
    else:
        return(redirect(url_for('sign_up')))


@app.route("/logout")
def logout():
    session.pop("name", None)
    session.pop("surname", None)
    session.pop("email", None)
    session.pop("password", None)
    return(redirect(url_for("login_page")))


if __name__ == "__main__":
    with app.app_context():
       db.create_all()
    app.run(debug=True)
