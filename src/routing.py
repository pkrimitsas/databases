from flask import render_template, flash, request, url_for, redirect, session
import mysql.connector
from src import app, db
import functools

def clear_session():
    session["is_admin"] = None
    session["username"] = None
    session["person_id"] = None
    session["activated"] = None
    session["husername"] = None
    session["hactivated"] = None

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session['username'] is None:
            return redirect(url_for('login'))
        
        return view(**kwargs)
    return wrapped_view

def admin_required(view):
    @functools.wraps(view)
    def admin_view(**kwargs):
        if session['is_admin'] is None:
            return redirect(url_for('index'))
        
        return view(**kwargs)
    return admin_view

def handler_required(view):
    @functools.wraps(view)
    def handler_view(**kwargs):
        if session['husername'] is None:
            return redirect(url_for('index'))
        
        return view(**kwargs)
    return handler_view

def account_activated(view):
    @functools.wraps(view)
    def activated_view(**kwargs):
        if session['activated'] is None:
            flash("Your account is not activated and you cannot view this page.")
            return redirect(url_for('index'))
        
        return view(**kwargs)
    return activated_view

@app.route("/admin_login", methods=('GET', 'POST'))
def admin_login():
    clear_session()
    if request.method == 'POST':
        if request.form['username'] != 'root' or request.form['password'] != 'admin':
            flash("Wrong credentials for user admin.")
            return redirect(url_for('index'))
        else:
            session['is_admin'] = 'T'
            return redirect(url_for('admin_page'))
        
    return render_template('admin_login.html')

@app.route("/")
def index():
    return render_template("base.html")

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        session['username'] = None
        session['person_id'] = None
        session['activated'] = None
        username1 = request.form['username']
        password1 = request.form['password']
        person_id1 = request.form['person_id']
        error = None

        if not username1:
            error = 'Username is required.'
        elif not password1:
            error = 'Password is required.'
        else :
            query = "SELECT person_id FROM user WHERE username = %s;"
            username = (username1,)
            cur = db.cursor()
            cur.execute(query, username)
            res = cur.fetchone()
            cur.close()
            if res is not None:
                error = 'User {} is already registered.'.format(username1)
                flash(error)
                return redirect(url_for('login'))

            if error is None:
                query = "SELECT person_type FROM person WHERE person_id = %s;"
                person_id = (person_id1,)
                cur=db.cursor()
                cur.execute(query, person_id)
                res = cur.fetchone()
                cur.close()
                is_student = ""
                if res[0] == "student":
                    is_student = "T"
                else:
                    is_student = "F"
                query = "insert into user(person_id, username, pass, is_active, is_student) values (%s, %s, %s, 'F', %s);"
                values = (person_id1, username1, password1, is_student)
                cur = db.cursor()
                cur.execute(query, values)
                db.commit()
                cur.close()
                return redirect(url_for('login'))
            
            flash(error)
    return render_template('register.html')

@app.route("/login", methods = ('GET', 'POST'))
def login():
    if request.method == 'POST':
        clear_session()
        username1 = request.form['username']
        password1 = request.form['password']
        query = "SELECT * FROM user WHERE username = %s;"
        username = (username1,)
        cur = db.cursor()
        cur.execute(query, username)
        res = cur.fetchone()
        cur.close()
        error = None
        if res is None:
            flash("User does not exist, register first")
            return redirect(url_for('register'))
        if username1 != res[1]:
            error = "Incorrent username."
        elif password1 != res[2]:
            error = "Incorrect password."
        elif 'T' != res[3]:
            error = "Account not activated, wait for the handler to activate your account."

        if error is None:
            session['username'] = request.form["username"]
            session['person_id'] = res[0]
            session['activated'] = "T"
            return redirect(url_for('books'))
        
        flash(error)

    return render_template('login.html')

@app.route("/logout")
def logout():
    clear_session()
    return redirect(url_for('index'))

@app.route("/show-users")
@login_required
def show_users():
    query = "SELECT first_name, last_name FROM person;"
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    persons = cur.fetchall()
    return render_template('show_users.html', persons = persons)

@app.route("/change_password", methods = ('GET', 'POST'))
@login_required
def change_password():
    if request.method == 'POST':
        new_pass = request.form['password']
        query = "UPDATE user SET pass = %s WHERE person_id = %s;"
        args = (new_pass, session['person_id'])
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()
        flash("Password changed successfully.")
        return redirect(url_for('login'))
    return render_template('change_password.html')

@app.route("/handler_login", methods = ('GET', 'POST'))
def handler_login():
    if request.method == 'POST':
        clear_session()
        username1 = request.form['username']
        password1 = request.form['password']
        query = "SELECT handler_password, handler_activated FROM school WHERE handler_username = %s;"
        username = (username1,)
        cur = db.cursor()
        cur.execute(query, username)
        res = cur.fetchone()
        cur.close()
        error = None
        if res is None:
            flash("This handler does not exist")
            return redirect(url_for('index'))
        if password1 != res[0]:
            error = "Incorrect password."
        elif 'T' != res[1]:
            error = "Handler not activated, wait for the admin to activate your account."

        if error is None:
            session["username"] = request.form["username"]
            session['husername'] = request.form["username"]
            session['hactivated'] = "T"
            return redirect(url_for('handler_page'))
        
        flash(error)

    return render_template('handler_login.html')

@app.route("/admin_page")
@admin_required
def admin_page():
    query = "SELECT school_id, handler_name, handler_surname, handler_username, handler_password, handler_activated FROM school;"
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    persons = cur.fetchall()
    return render_template('admin_page.html', handlers=persons)

@app.route("/<int:school_id>/hactivate", methods=('POST', 'GET'))
def hactivate(school_id):
    if request.method == 'POST':
        query = "UPDATE school SET handler_activated = 'T' WHERE school_id = %s;"
        args = (school_id,)
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()
        return redirect(url_for('admin_page'))
    
    return render_template('admin_page.html')

@app.route("/<int:school_id>/hdeactivate", methods=('POST', 'GET'))
def hdeactivate(school_id):
    if request.method == 'POST':
        query = "UPDATE school SET handler_activated = 'F' WHERE school_id = %s;"
        args = (school_id,)
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()
        return redirect(url_for('admin_page'))
    
    return render_template('admin_page.html')

@app.route("/handler_page")
@handler_required
def handler_page():
    query = "SELECT person_id, username, pass, is_active FROM user;"
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    users = cur.fetchall()
    return render_template('handler_page.html', persons=users)

@app.route("/<int:person_id>/pactivate", methods=('POST', 'GET'))
def pactivate(person_id):
    if request.method == 'POST':
        query = "UPDATE user SET is_active = 'T' WHERE person_id = %s;"
        args = (person_id,)
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()
        return redirect(url_for('handler_page'))
    
    return render_template('handler_page.html')

@app.route("/<int:person_id>/pdeactivate", methods=('POST', 'GET'))
def pdeactivate(person_id):
    if request.method == 'POST':
        query = "UPDATE user SET is_active = 'F' WHERE person_id = %s;"
        args = (person_id,)
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()
        return redirect(url_for('handler_page'))
    
    return render_template('handler_page.html')

@app.route("/books")
@login_required
def books():
    query = "SELECT * FROM review;"
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    reviews = cur.fetchall()
    cur.close()
    query = "SELECT * FROM book;"
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    books = cur.fetchall()
    cur.close()
    for book in books:
        query = "SELECT school_name FROM school WHERE school_id = %s;"
        arg = (book['school_id'],)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, arg)
        res = cur.fetchone()
        cur.close()
        book['school_id'] = res['school_name']
    return render_template('books.html', books=books, reviews=reviews)

@app.route("/<string:ISBN>/add_review", methods=('GET', 'POST'))
@login_required
def add_review(ISBN):
    if request.method == 'POST':
        query = "SELECT review_id FROM review ORDER BY review_id DESC;"
        cur = db.cursor()
        cur.execute(query)
        res = cur.fetchone()
        cur.close()
        if res is None:
            id = 1
        else:
            id = res[0]
        text = request.form['text']
        user = session["username"]
        query = "INSERT INTO review(review_id, ISBN, username, opinion, is_approved) VALUES (%s, %s, %s, %s, 'F');"
        args = (id, ISBN, user, text)
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()
        flash("Your review has been registered successfully.")
        return redirect(url_for('books'))
    return render_template('add_review.html')

@app.route("/<string:ISBN>/view_reviews")
@handler_required
def view_reviews(ISBN):
    query = "SELECT * FROM review WHERE ISBN = %s;"
    args = (ISBN,)
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query, args)
    reviews = cur.fetchall()
    return render_template('view_reviews.html', reviews=reviews)

@app.route("/<int:review_id>/ractivate", methods=('GET', 'POST'))
@handler_required
def ractivate(review_id):
    if request.method == 'POST':
        query = "UPDATE review SET is_approved = 'T' WHERE review_id = %s;"
        args = (review_id,)
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()
        flash("Review was approved for posting successfully.")
        return redirect(url_for('books'))
    
    return render_template('books.html')

@app.route("/<int:review_id>/rdeactivate", methods=('GET', 'POST'))
@handler_required
def rdeactivate(review_id):
    if request.method == 'POST':
        query = "DELETE FROM review WHERE review_id = %s;"
        args = (review_id,)
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()
        flash("Review was deleted successfully.")
        return redirect(url_for('books'))
    
    return render_template('books.html')