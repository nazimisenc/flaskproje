from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,IntegerField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

#Kullanıcı Giriş Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please login to view this page!","danger")
            return redirect(url_for("login"))

    return decorated_function

#Kullanıcı Çıkış Decorator
def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            flash("Please logout to view this page!","danger")
            return redirect(url_for("index"))
        else:
            return f(*args, **kwargs)
            

    return decorated_function






#Kullanıcı Kayıt Formu
class RegisterForm(Form):
    name = StringField("Name Surname:",validators=[validators.Length(min=4,max=24)])
    username = StringField("Username:",validators=[validators.Length(min=4,max=34)])
    email = StringField("Email Address:",validators=[validators.Email(message="Please enter a correct email address!")])
    password = PasswordField("Password:",validators=[
        validators.DataRequired(message="Please enter a password!"),
        validators.EqualTo(fieldname="confirm",message="Your password does not match!")
        ])
    confirm = PasswordField("Password Verify:")
class LoginForm(Form):
    username = StringField("Username:")
    password = PasswordField("Password:")




app = Flask(__name__)
app.secret_key = "oxer"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "oxer"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)



@app.route('/')
def index():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From classes"
    cursor.execute(sorgu)
    classes = cursor.fetchall()
    
    
    return render_template('index.html',classes = classes)

@app.route("/complated")
@login_required
def complated():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From deneme where admin = %s"
    result = cursor.execute(sorgu,(session["username"],)) 

    if result > 0:
        sorgu2 = "Insert into carts(id,centername,coachname,phone,location,price,admin,owner) Select id,centername,coachname,phone,location,price,admin,owner From deneme where admin = %s"
        cursor.execute(sorgu2,(session["username"],))
        mysql.connection.commit()
        
        flash("Payment Succesfully Complated!","success")
        return redirect(url_for("profile"))

    else:
        flash("Payment Failed!","danger")
        return redirect(url_for("cart"))
    

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/class")
def classes():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From classes"
    result = cursor.execute(sorgu)
    
    if result>0:
        classes = cursor.fetchall()
        
        return render_template("class.html",classes = classes)
    else:
        return render_template("class.html")

@app.route("/blog")
def blog():
    return render_template('blog.html')

#Register
@app.route("/register",methods = ["GET","POST"])
@logout_required
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        
        cursor = mysql.connection.cursor()
        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        
        flash("Succesfully Registered!","success")
        
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form=form)


#Login
@app.route("/login",methods = ["GET","POST"])
@logout_required
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
        
        cursor = mysql.connection.cursor()
        sorgu = "Select * From users where username = %s"
        result = cursor.execute(sorgu,(username,))
        if result>0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Succesfully Logged!","success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Wrong password entered!","danger")
                return redirect(url_for("login"))
        else:
            flash("Wrong username entered!","danger")
            return redirect(url_for("login"))
        
        
    return render_template("login.html",form = form)

#Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#Dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From classes where admin = %s"
    result = cursor.execute(sorgu,(session["username"],))
    if result > 0:
        classes = cursor.fetchall()
        return render_template("dashboard.html",classes = classes)
    else:
        return render_template("dashboard.html")

#Addtocart
@app.route("/addtocart/<string:id>")
@login_required
def addtocart(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * From classes where id = %s"
    result = cursor.execute(sorgu,(id,)) 

    if result > 0:
        sorgu2 = "Insert into deneme(id,centername,coachname,phone,location,price,admin,owner) Select id,centername,coachname,phone,location,price,%s,admin From classes where id = %s"
        cursor.execute(sorgu2,(session["username"],id))
        mysql.connection.commit()
        
        flash("Successfully added to cart!","success")
        return redirect(url_for("classes"))

    else:
        flash("You can't add this!","danger")
        return redirect(url_for("classes"))

#Buy Page
@app.route("/buy")
@login_required
def buy():
    return render_template("buy.html")


#Detail Coach Page
@app.route("/coach/<string:id>")
def coach(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * From classes where id = %s"
    result = cursor.execute(sorgu,(id,))
    if result > 0:
        coachclass = cursor.fetchone()
        return render_template("coach.html",coachclass = coachclass)
    else:
        return render_template("coach.html")



#Add Class
@app.route("/addboxingcenter",methods = ["GET","POST"])
def addclass():
    form = ClassForm(request.form)
    if request.method == "POST" and form.validate():
        centername = form.centername.data
        coachname = form.coachname.data
        phone = form.phone.data
        location = form.location.data
        price = form.price.data
        aboutcoach = form.aboutcoach.data
        
        cursor = mysql.connection.cursor()
        sorgu = "Insert into classes(centername,coachname,phone,location,price,aboutcoach,admin) VALUES(%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(sorgu,(centername,coachname,phone,location,price,aboutcoach,session["username"]))
        mysql.connection.commit()
        cursor.close()
        
        flash("Boxing Center Succesfully Added!","success")
        return redirect(url_for("dashboard"))
        
    return render_template("addboxingcenter.html",form = form)

#Class Delete
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * From classes where admin = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id))
    if result > 0:
        sorgu2 = "Delete from classes where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        
        return redirect(url_for("dashboard"))
        
    else:
        flash("You can't delete this Boxing Center!","danger")
        return redirect(url_for("index"))
    
#Cart Delete
@app.route("/remove/<string:id>")
@login_required
def remove(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * From deneme where admin = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id))
    if result > 0:
        sorgu2 = "Delete From deneme where id = %s and admin = %s"
        cursor.execute(sorgu2,(id,session["username"]))
        mysql.connection.commit()
        
        return redirect(url_for("cart"))
        
    else:
        flash("You can't remove this!","danger")
        return redirect(url_for("cart"))    
    
#Class Update
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select * from classes where id = %s and admin = %s"
        result = cursor.execute(sorgu,(id,session["username"]))
        if result == 0:
            flash("You can't this operation!","danger")
            return redirect(url_for("index"))
        else:
            classes = cursor.fetchone()
            form = ClassForm()
            
            form.centername.data = classes["centername"]
            form.coachname.data = classes["coachname"]
            form.phone.data = classes["phone"]
            form.location.data = classes["location"]
            form.price.data = classes["price"]
            form.aboutcoach.data = classes["aboutcoach"]
            
            return render_template("update.html",form=form)
        
    else:
        #Post request
        form = ClassForm(request.form)
        newCemterName = form.centername.data
        newCoachName = form.coachname.data
        newPhone = form.phone.data
        newLocation = form.location.data
        newPrice = form.price.data
        newAboutCoach = form.aboutcoach.data
        
        sorgu2 = "Update classes Set centername = %s,coachname = %s,phone = %s,location =%s,price = %s,aboutcoach = %s where id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newCemterName,newCoachName,newPhone,newLocation,newPrice,newAboutCoach,id))
        mysql.connection.commit()
        flash("Boxing Center Updated Successfully!","success")
        return redirect(url_for("dashboard"))
    
#Cart        
@app.route("/cart")
@login_required
def cart():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From deneme where admin = %s"
    result = cursor.execute(sorgu,(session["username"],))
    
    if result>0:
        classes = cursor.fetchall()
        toplamprice = 0
        for row in classes:
            toplamprice += row["price"]
            
        return render_template("cart.html",classes = classes,toplamprice = toplamprice)
    else:
        return render_template("cart.html")
            
#Profile
@app.route("/profile")
@login_required
def profile():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From users where username = %s"
    result = cursor.execute(sorgu,(session["username"],))
    
    if result > 0:
        users = cursor.fetchone()
        
        sorgu2 = "Select * From carts where admin = %s"
        cursor.execute(sorgu2,(session["username"],))
        complatedorders = cursor.fetchall()
        
        sorgu3 = "Select * From carts where owner = %s"
        cursor.execute(sorgu3,(session["username"],))
        owners = cursor.fetchall()
        
        mysql.connection.commit()
        return render_template("profile.html",complatedorders = complatedorders,users = users,owners = owners )
    else:
         return render_template("profile.html")
     
        
#Class Form
class ClassForm(Form):
    centername = StringField("Boxing Center Name:",validators=[validators.Length(min=3,max=100)])
    coachname = StringField("Coach Name:",validators=[validators.Length(min=3,max=20)])
    phone =  StringField("Phone:",validators=[validators.Length(min=11,max=11)])
    location =  StringField("Location:",validators=[validators.Length(min=3,max=20)])
    price = IntegerField("Price:",validators=[validators.NumberRange(min=1)])
    aboutcoach = TextAreaField("Introduce Coach:",validators=[validators.Length(min=10,max=500)])
    
#Search URL
@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        sorgu = "Select * from classes where centername like '%" + keyword +"%'"
        result = cursor.execute(sorgu)
        if result == 0:
            flash("Doesn't find anything!","warning")
            return redirect(url_for("classes"))
        else:
            classes = cursor.fetchall()
            return render_template("class.html",classes = classes)


if __name__ == '__main__':
    app.run(debug=True)