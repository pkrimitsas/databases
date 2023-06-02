from flask import render_template, flash, request, url_for, redirect, session
#import mysql.connector
from src import app, db
import functools
import datetime
import os

def update_reservations():
    query = "SELECT * FROM reservations;"
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    reservations = cur.fetchall()
    cur.close()
    current_time = datetime.datetime.now().replace(microsecond=0)
    curr = db.cursor()
    for reservation in reservations:
        # we dont want to mark as over the reservation made by users because no copies were available
        # we only want the reservations that are active and the time has passed
        # to be marked as over
        if reservation['rdate'] < current_time and reservation['is_active'] == 'T':
            query = "UPDATE reservations SET is_active = 'F', is_over = 'T' WHERE reservation_id = %s;"
            args = (reservation['reservation_id'])
            curr.execute(query, args)

    db.commit()
    curr.close()


def update_table():
    query = "SELECT * FROM currently_available;"
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    current = cur.fetchall()
    cur.close()
    for x in current:
        ISBN = x['ISBN']
        query = "SELECT * FROM book WHERE ISBN = %s;"
        cur = db.cursor(buffered=True, dictionary=True)
        args = (ISBN,)
        cur.execute(query, args)
        cp = cur.fetchone()
        cur.close()
        copies = cp['copies']
        query = "SELECT * FROM now_borrowed WHERE ISBN = %s AND is_returned = 'F';"
        cur = db.cursor(buffered=True, dictionary=True)
        args = (ISBN,)
        cur.execute(query, args)
        res = cur.fetchall()
        cur.close()
        query = "SELECT * FROM reservations WHERE ISBN = %s AND is_active = 'T' AND is_over = 'F';"
        cur = db.cursor(buffered=True, dictionary=True)
        args = (ISBN,)
        cur.execute(query, args)
        res2 = cur.fetchall()
        cur.close()
        diff = copies - len(res) - len(res2)
        query = "UPDATE currently_available SET current = %s WHERE ISBN = %s;"
        args = (diff, ISBN)
        curr = db.cursor()
        curr.execute(query, args)
    
    db.commit()
    curr.close()



def checkInt(str):
  if str[0] in ('-', '+'):
    return str[1:].isdigit()
  return str.isdigit()

def clear_session():
    session["is_admin"] = None
    session["username"] = None
    session["person_id"] = None
    session["activated"] = None
    session["husername"] = None
    session["hactivated"] = None
    session['school_id'] = None

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session['username'] is None:
            flash("You are not logged in and cannot view this page.")
            clear_session()
            return redirect(url_for('login'))
        
        return view(**kwargs)
    return wrapped_view

def admin_required(view):
    @functools.wraps(view)
    def admin_view(**kwargs):
        if session['is_admin'] is None:
            flash("You are not an admin and cannot view this page, logging you out.")
            clear_session()
            return redirect(url_for('index'))
        
        return view(**kwargs)
    return admin_view

def handler_required(view):
    @functools.wraps(view)
    def handler_view(**kwargs):
        if session['husername'] is None:
            flash("You are not a handler and cannot view this page, logging you out.")
            clear_session()
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
    update_reservations()
    clear_session()
    if request.method == 'POST':
        if request.form['username'] != 'root' or request.form['password'] != 'admin':
            flash("Wrong credentials for user admin.")
            return redirect(url_for('index'))
        else:
            session['is_admin'] = 'T'
            session['username'] = 't'
            return redirect(url_for('admin_page'))
        
    return render_template('admin_login.html')

@app.route("/register-school", methods=('GET', 'POST'))
@admin_required
def register_school():
    if request.method == 'POST':
        school_name = request.form['school_name']
        address = request.form['address']
        city = request.form['city']
        phone = request.form['phone']
        email = request.form['email']
        dname = request.form['dname']
        dsur = request.form['dsur']
        hname = request.form['hname']
        hsur = request.form['hsur']
        hac = request.form['hact']

        huser = request.form['huser']
        hpass = request.form['hpass']

        if hac != 'T' and hac != 'F':
            flash("Invalid value for Handler Activated Account.")
            return redirect(url_for('register_school'))
        
        if not checkInt(phone) or int(phone) <= 0:
            flash("This phone number is not valid.")
            return redirect(url_for('register_school'))

        query = """INSERT INTO school(school_id, school_name, address_name, city, phone_number, email, director_name, 
                    director_surname, handler_name, handler_surname, handler_activated) 
                    VALUES (0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
        
        args = (school_name, address, city, phone, email, dname, dsur, hname, hsur, hac)
        cur = db.cursor()
        
        cur.execute(query, args)

        query = "SELECT school_id FROM school ORDER BY school_id DESC LIMIT 1;"
        cur.execute(query)
        res = cur.fetchone()
        school_id = res[0] 

        query = """INSERT INTO person(person_id, school_id, first_name, last_name, sex, person_type, age) VALUES
                                        (0, %s, %s, %s, 'update', 'update', 1);"""
        
        args = (school_id, hname, hsur)
        cur.execute(query, args)

        query = "SELECT person_id FROM person ORDER BY person_id DESC LIMIT 1;"
        cur.execute(query)
        res = cur.fetchone()
        pid = int(res[0])

        query = """INSERT INTO handlers(person_id, school_id, handler_name, handler_surname, handler_username, handler_password)
                    VALUES (%s, %s, %s, %s, %s, %s);"""
        
        args = (pid, school_id, hname, hsur, huser, hpass)
        cur.execute(query, args)

        db.commit()
        cur.close()
        
        flash("New school was addedd successfully.")
        return redirect(url_for('admin_page'))
    

    return render_template("register_school.html")

@app.route("/")
def index():
    update_reservations()
    return render_template("base.html")

@app.route('/register', methods=('GET', 'POST'))
def register():
    update_reservations()
    if request.method == 'POST':
        clear_session()
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
            
            query = "SELECT * FROM handlers WHERE person_id = %s"
            cur = db.cursor()
            args = (person_id1,)
            cur.execute(query, args)
            res2 = cur.fetchall()
            cur.close()
            if len(res2) != 0:
                error = "The person with this person ID is a handler."

            query = "SELECT * FROM user WHERE person_id = %s"
            cur = db.cursor()
            args = (person_id1,)
            cur.execute(query, args)
            res2 = cur.fetchall()
            cur.close()
            if len(res2) != 0:
                error = "User with this person_id is already registered."

            if error is None:
                query = "SELECT person_type, school_id FROM person WHERE person_id = %s;"
                person_id = (person_id1,)
                cur=db.cursor()
                cur.execute(query, person_id)
                res = cur.fetchone()
                cur.close()
                is_student = ""
                if res is None:
                    error = "Person with this person_id does not exist (handler should create the person first)"
                    flash(error)
                    return redirect(url_for('index'))
                if res[0] == "student":
                    is_student = "T"
                else:
                    is_student = "F"
                query = "insert into user(person_id, username, pass, is_active, is_student, school_id) values (%s, %s, %s, 'F', %s, %s);"
                values = (person_id1, username1, password1, is_student, res[1])
                cur = db.cursor()
                cur.execute(query, values)
                db.commit()
                cur.close()
                flash("Registered successfully, wait for the handler to activate your account.")
                return redirect(url_for('login'))
            
            flash(error)
    return render_template('register.html')

@app.route("/login", methods = ('GET', 'POST'))
def login():
    update_reservations()
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
    update_reservations()
    clear_session()
    return redirect(url_for('index'))

@app.route("/show-users")
@login_required
def show_users():
    update_reservations()
    query = "SELECT first_name, last_name FROM person;"
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    persons = cur.fetchall()
    return render_template('show_users.html', persons = persons)

@app.route("/change_password", methods = ('GET', 'POST'))
@login_required
def change_password():
    update_reservations()
    if request.method == 'POST':
        if session['husername'] is None or session['husername'] == '':
            new_pass = request.form['password']
            query = "UPDATE user SET pass = %s WHERE person_id = %s;"
            args = (new_pass, session['person_id'])
            cur = db.cursor()
            cur.execute(query, args)
            db.commit()
            cur.close()
            flash("Password changed successfully.")
            clear_session()
            return redirect(url_for('login'))
        else :
            new_pass = request.form['password']
            query = "UPDATE handlers SET handler_password = %s WHERE person_id = %s;"
            args = (new_pass, session['person_id'])
            cur = db.cursor()
            cur.execute(query, args)
            db.commit()
            cur.close()
            flash("Password changed successfully.")
            clear_session()
            return redirect(url_for('handler_login'))
    return render_template('change_password.html')

@app.route("/add_person", methods=('POST', 'GET'))
@handler_required
def add_person():
    if request.method == 'POST':
        sid = session['school_id']
        name = request.form['name']
        lname = request.form['lname']
        sex = request.form['sex']
        age = request.form['age']
        ptype = request.form['type']

        query = "INSERT INTO person(person_id, school_id, first_name, last_name, sex, person_type, age) VALUES (0, %s, %s, %s, %s, %s, %s);"
        args = (sid, name, lname, sex, ptype, age)
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()

        query = "SELECT person_id FROM person ORDER BY person_id DESC LIMIT 1;"
        cur = db.cursor()
        cur.execute(query)
        res = cur.fetchone()
        cur.close()

        flash(f"Person Id of newly created person is {res[0]}")
        return redirect(url_for('handler_page'))
    
    return render_template("add_person.html")

@app.route("/handler_login", methods = ('GET', 'POST'))
def handler_login():
    update_reservations()
    if request.method == 'POST':
        clear_session()
        username1 = request.form['username']
        password1 = request.form['password']
        query = "SELECT person_id, handler_password, school_id FROM handlers WHERE handler_username = %s;"
        username = (username1,)
        cur = db.cursor()
        cur.execute(query, username)
        res = cur.fetchone()
        cur.close()
        if res is None or len(res) == 0:
            flash("No handler with this username exists.")
            return redirect(url_for('index'))
        query = "SELECT handler_activated FROM school WHERE school_id = %s;"
        args = (res[2],)
        cur = db.cursor()
        cur.execute(query, args)
        res2 = cur.fetchone()
        cur.close()
        error = None
        if res is None:
            flash("This handler does not exist")
            return redirect(url_for('index'))
        if password1 != res[1]:
            error = "Incorrect password."
        elif 'T' != res2[0]:
            error = "Handler not activated, wait for the admin to activate your account."

        if error is None:
            session["username"] = request.form["username"]
            session['husername'] = request.form["username"]
            session['hactivated'] = "T"
            session['school_id'] = res[2]
            session['person_id'] = res[0]
            return redirect(url_for('handler_page'))
        
        flash(error)

    return render_template('handler_login.html')

@app.route("/admin_page")
@admin_required
def admin_page():
    update_reservations()
    query = "SELECT school_id, handler_name, handler_surname, handler_activated FROM school;"
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    persons = cur.fetchall()
    return render_template('admin_page.html', handlers=persons)

@app.route("/<int:school_id>/hactivate", methods=('POST', 'GET'))
@admin_required
def hactivate(school_id):
    update_reservations()
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
@admin_required
def hdeactivate(school_id):
    update_reservations()
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
    update_reservations() 
    query = "SELECT person_id, username, pass, is_active FROM user WHERE school_id = %s;"
    args = (session['school_id'],)
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query, args)
    users = cur.fetchall()
    return render_template('handler_page.html', persons=users)

@app.route("/<int:person_id>/pactivate", methods=('POST', 'GET'))
@handler_required
def pactivate(person_id):
    update_reservations()
    if request.method == 'POST':
        query = "UPDATE user SET is_active = 'T' WHERE person_id = %s;"
        args = (person_id,)
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()
        flash("Account activated successfully.")
        return redirect(url_for('handler_page'))
    
    return render_template('handler_page.html')

@app.route("/<int:person_id>/pdeactivate", methods=('POST', 'GET'))
@handler_required
def pdeactivate(person_id):
    update_reservations()
    if request.method == 'POST':
        query = "UPDATE user SET is_active = 'F' WHERE person_id = %s;"
        args = (person_id,)
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()
        flash("Account deactivated successfully.")
        return redirect(url_for('handler_page'))
    
    return render_template('handler_page.html')

@app.route("/<int:person_id>/pdelete", methods=('POST', 'GET'))
@handler_required
def pdelete(person_id):
    update_reservations()
    if request.method == 'POST':
        query = "DELETE FROM user WHERE person_id = %s;"
        args = (person_id,)
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()
        flash("User deleted successfully.")
        return redirect(url_for('handler_page'))
    
    return render_template('handler_page.html')

@app.route("/books")
@login_required
def books():
    update_reservations()
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
    query = "SELECT * FROM currently_available;"
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    current = cur.fetchall()
    cur.close()
    query = "SELECT * FROM theme;"
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    themes = cur.fetchall()
    cur.close()
    return render_template('books.html', books=books, reviews=reviews, current=current, themes=themes)

@app.route("/<string:ISBN>/add_review", methods=('GET', 'POST'))
@login_required
def add_review(ISBN):
    update_reservations()
    if request.method == 'POST':

        text = request.form['text']
        if request.form['rating'] == 'one':
            scale = 1
        elif request.form['rating'] == "two":
            scale = 2
        elif request.form['rating'] == "three":
            scale = 3
        elif request.form['rating'] == "four":
            scale = 4
        elif request.form['rating'] == "five":
            scale = 5
        user = session["username"]
        query = "INSERT INTO review(review_id, ISBN, username, opinion, is_approved, scale) VALUES (0, %s, %s, %s, 'F', %s);"
        args = (ISBN, user, text, scale)
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
    update_reservations()
    query = "SELECT * FROM review WHERE ISBN = %s;"
    args = (ISBN,)
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query, args)
    reviews = cur.fetchall()
    return render_template('view_reviews.html', reviews=reviews)

@app.route("/<int:review_id>/ractivate", methods=('GET', 'POST'))
@handler_required
def ractivate(review_id):
    update_reservations()
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
    update_reservations()
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

@app.route("/<int:person_id>/my_profile", methods=('POST', 'GET'))
@login_required
def my_profile(person_id):
    update_reservations()
    if request.method == 'GET':
        query = "SELECT * FROM person WHERE person_id = %s;"
        args = (person_id,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        person = cur.fetchone()
        cur.close()
        query = "SELECT * FROM user WHERE person_id = %s;"
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        user = cur.fetchone()
        cur.close()
        query = "SELECT * FROM handlers WHERE person_id = %s;"
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        handler = cur.fetchone()
        cur.close()
        return render_template('my_profile.html', person=person, user=user, handler=handler)
    else :
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        sex = request.form['sex']
        username = request.form['username1']
        query = "SELECT first_name, last_name, sex FROM person WHERE person_id = %s;"
        args = (person_id,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        person = cur.fetchone()
        cur.close()
        if session['husername'] is None or session['husername'] == '':
            query = "SELECT username FROM user WHERE person_id = %s;"
            args = (person_id,)
            cur = db.cursor(buffered=True, dictionary=True)
            cur.execute(query, args)
            user = cur.fetchone()
            cur.close()
            if username == '':
                username = user['username']
        else :
            query = "SELECT handler_username FROM handlers WHERE person_id = %s;"
            args = (person_id,)
            cur = db.cursor(buffered=True, dictionary=True)
            cur.execute(query, args)
            handler = cur.fetchone()
            cur.close()
            if username == '':
                username = handler['handler_username']
        if first_name == '':
            first_name = person['first_name']
        if last_name == '':
            last_name = person['last_name']
        if sex == '':
            sex = person['sex']
        if session['husername'] is None or session['husername'] == '':
            query = "UPDATE user SET username = %s WHERE person_id = %s;"
            args = (username, person_id)
            cur = db.cursor()
            cur.execute(query, args)
            db.commit()
            cur.close()
            query = "UPDATE person SET first_name = %s, last_name = %s, sex = %s WHERE person_id = %s;"
            args = (first_name, last_name, sex, person_id)
            cur = db.cursor()
            cur.execute(query, args)
            db.commit()
            cur.close()
        else :
            query = "UPDATE handlers SET handler_username = %s WHERE person_id = %s;"
            args = (username, person_id)
            cur = db.cursor()
            cur.execute(query, args)
            db.commit()
            cur.close()
            query = "UPDATE school SET handler_name = %s, handler_surname = %s WHERE school_id = %s;"
            args = (first_name, last_name, session['school_id'])
            cur = db.cursor()
            cur.execute(query, args)
            db.commit()
            cur.close()
            query = "UPDATE person SET first_name = %s, last_name = %s, sex = %s WHERE person_id = %s;"
            args = (first_name, last_name, sex, person_id)
            cur = db.cursor()
            cur.execute(query, args)
            db.commit()
            cur.close()
        query = "SELECT * FROM person WHERE person_id = %s;"
        args = (person_id,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        person = cur.fetchone()
        cur.close()
        query = "SELECT * FROM user WHERE person_id = %s;"
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        user = cur.fetchone()
        cur.close()
        query = "SELECT * FROM handlers WHERE person_id = %s;"
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        handler = cur.fetchone()
        cur.close()
        flash("Changes were made successfully.")
        return render_template('my_profile.html', person=person, user=user, handler=handler)
    
@app.route("/<string:ISBN>/edit_book", methods=('GET', 'POST'))
@handler_required
def edit_book(ISBN):
    update_reservations()
    if request.method == 'GET':
        query = "SELECT * FROM book WHERE ISBN = %s AND school_id = %s;"
        args = (ISBN, session['school_id'])
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        book = cur.fetchone()
        cur.close()
        return render_template('edit_book.html', book=book)
    else:
        try:
            title = request.form['title']
            publisher = request.form['publisher']
            author = request.form['author']
            pages = request.form['pages']
            summary = request.form['summary']
            copies = request.form['copies']
            picture = request.form['picture']
            language = request.form['language']
            keywords = request.form['keywords']
            query = "SELECT * FROM book WHERE ISBN = %s;"
            args = (ISBN,)
            cur = db.cursor(buffered=True, dictionary=True)
            cur.execute(query, args)
            book = cur.fetchone()
            cur.close()
            if title == '':
                title = book['title']
            if publisher == '':
                publisher = book['publisher']
            if author == '':
                author = book['author']
            if pages == '':
                pages = book['pages']
            if summary == '':
                summary = book['summary']
            if copies == '':
                copies = book['copies']
            if picture == '':
                picture = book['picture']
            if language == '':
                language = book['blanguage']
            if keywords == '':
                keywords = book['keywords']
            if len(title) > 199 or len(publisher) > 49 or len(author) > 49 or len(language) > 49:
                flash("One of the fields you provided is too long.")
                return render_template('edit_book.html', book=book)
            query = 'UPDATE book SET title = %s, publisher = %s, author = %s, pages = %s, summary = %s, copies = %s, picture = %s, blanguage = %s, keywords = %s WHERE ISBN = %s;'
            args = (title, publisher, author, pages, summary, copies, picture, language, keywords, ISBN)
            cur = db.cursor()
            cur.execute(query, args)
            db.commit()
            cur.close()
            flash("Book was updated successfully.")
            return redirect(url_for('edit_book', ISBN=ISBN))
        except Exception as e:
            flash(e)
            #flash(copies)
            #flash(book['copies'])
            query = "SELECT * FROM book WHERE ISBN = %s;"
            args = (ISBN,)
            cur = db.cursor(buffered=True, dictionary=True)
            cur.execute(query, args)
            book = cur.fetchone()
            cur.close()
            return render_template('edit_book.html', book=book)
        
@app.route("/add_book", methods=('GET', 'POST'))
@handler_required
def add_book():
    update_reservations()
    if request.method == 'POST':
        school_id = session['school_id']
        title = request.form['title']
        publisher = request.form['publisher']
        isbn = request.form['ISBN']
        author = request.form['author']
        pages = request.form['pages']
        summary = request.form['summary']
        copies = request.form['copies']
        picture = request.form['picture']
        language = request.form['language']
        keywords = request.form['keywords']
        theme1 = request.form['theme1']
        theme2 = request.form['theme2']
        theme3 = request.form['theme3']
        query = "SELECT school_name FROM school WHERE school_id = %s;"
        args = (session['school_id'],)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        name = cur.fetchone()
        cur.close()
        query = "INSERT INTO book(school_id, title, publisher, ISBN, author, pages, summary, copies, picture, blanguage, keywords, school_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        args = (school_id, title, publisher, isbn, author, pages, summary, copies, picture, language, keywords, name['school_name'])
        cur = db.cursor()
        try:
            cur.execute(query, args)
            db.commit()
            cur.close()

            query = "INSERT INTO theme(indexer, ISBN, theme_name) VALUES (0, %s, %s);"
            args = (isbn, theme1)
            cur = db.cursor()
            cur.execute(query, args)
            if theme2 != '':
                args = (isbn, theme2)
                cur.execute(query, args)
            if theme3 != '':
                args = (isbn, theme3)
                cur.execute(query, args)

            # also add to currently_available
            query = "INSERT INTO currently_available(ISBN, current) VALUES (%s, %s);"
            args = (isbn, copies)
            cur.execute(query, args)
            db.commit()
            cur.close()
            flash("Your book was addedd successfully.")
            return redirect(url_for('books'))
        except Exception as e:
            flash(e)
            return render_template('add_book.html')
        
    return render_template('add_book.html')

@app.route("/search", methods=('GET', 'POST'))
@login_required
def search():
    update_reservations()
    if request.method == 'POST':
        title = request.form['title']
        theme = request.form['theme']
        author = request.form['author']
        if session['husername'] is not None:
            copies = request.form['copies']
        query = "SELECT * FROM currently_available;"
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query)
        current = cur.fetchall()
        cur.close()
        if session['husername'] is None:
            if title != '':
                query = "SELECT * FROM book WHERE title = %s;"
                args = (title,)
                cur = db.cursor(buffered=True, dictionary=True)
                cur.execute(query, args)
                res = cur.fetchall()
                cur.close()
                if len(res) == 0:
                    flash("No book with the title you provided exists in our database.")
                    return redirect(url_for('search'))
                else:
                    if theme != '':
                        if author != '':
                            # title author and theme are not NULL
                            books = []
                            query = "SELECT * FROM book WHERE title = %s AND author = %s;"
                            cur = db.cursor(buffered=True, dictionary=True)
                            args = (title, author)
                            cur.execute(query, args)
                            book = cur.fetchall()
                            cur.close()
                            if len(book) == 0:
                                flash("No book with the title and author you provided exists.")
                                return redirect(url_for('search'))

                            for b in book:
                                isbn = b['ISBN']
                                query = "SELECT * FROM theme WHERE ISBN = %s AND theme_name = %s;"
                                cur = db.cursor(buffered=True, dictionary=True)
                                args = (isbn, theme)
                                cur.execute(query, args)
                                ans = cur.fetchall()
                                if len(ans) == 0:
                                    continue
                                else :
                                    curr = db.cursor(buffered=True, dictionary=True)
                                    query = "SELECT * FROM book WHERE ISBN = %s;"
                                    args = (isbn,)
                                    curr.execute(query, args)
                                    books = books + curr.fetchall()
                                    curr.close()
                                cur.close()
                            
                            if len(books) == 0:
                                flash("No book with all the parameters you specified exists.")
                                return redirect(url_for('search'))
                            
                            reviews = []
                            for x in books:
                                query = "SELECT * FROM review WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                reviews = reviews + cur.fetchall()
                                cur.close()
                            
                            themes = []
                            for x in books:
                                query = "SELECT * FROM theme WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                themes = themes + cur.fetchall()
                                cur.close()

                            flash("Success!")
                            return render_template("results.html", books=books, reviews=reviews, current=current, themes=themes)
                        else :
                            # title and theme are not NULL, author is NULL
                            books = []
                            query = "SELECT * FROM book WHERE title = %s;"
                            cur = db.cursor(buffered=True, dictionary=True)
                            args = (title,)
                            cur.execute(query, args)
                            book = cur.fetchall()
                            cur.close()
                            if len(book) == 0:
                                flash("No book with the title you provided exists.")
                                return redirect(url_for('search'))
                            

                            for b in book:
                                isbn = b['ISBN']
                                query = "SELECT * FROM theme WHERE ISBN = %s AND theme_name = %s;"
                                cur = db.cursor(buffered=True, dictionary=True)
                                args = (isbn, theme)
                                cur.execute(query, args)
                                ans = cur.fetchall()
                                if len(ans) == 0:
                                    continue
                                else :
                                    curr = db.cursor(buffered=True, dictionary=True)
                                    query = "SELECT * FROM book WHERE ISBN = %s;"
                                    args = (isbn,)
                                    curr.execute(query, args)
                                    books = books + curr.fetchall()
                                    curr.close()
                                cur.close()
                            
                            if len(books) == 0:
                                flash("No book with all the parameters you specified exists.")
                                return redirect(url_for('search'))
                            
                            reviews = []
                            for x in books:
                                query = "SELECT * FROM review WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                reviews = reviews + cur.fetchall()
                                cur.close()

                            themes = []
                            for x in books:
                                query = "SELECT * FROM theme WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                themes = themes + cur.fetchall()
                                cur.close()

                            flash("Success")
                            return render_template("results.html", books=books, reviews=reviews, current=current, themes=themes)
                    else :
                        if author != '':
                            # title and author are not NULL, theme is NULL
                            query = "SELECT * FROM book WHERE title = %s AND author = %s;"
                            cur = db.cursor(buffered=True, dictionary=True)
                            args = (title, author)
                            cur.execute(query, args)
                            book = cur.fetchall()
                            cur.close()
                            if len(book) == 0:
                                flash("No book with the title and author you provided exists.")
                                return redirect(url_for('search'))
                            
                            reviews = []
                            for x in book:
                                query = "SELECT * FROM review WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                reviews = reviews + cur.fetchall()
                                cur.close()

                            themes = []
                            for x in book:
                                query = "SELECT * FROM theme WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                themes = themes + cur.fetchall()
                                cur.close()

                            flash("Success")
                            return render_template("results.html", books=book, reviews=reviews, current=current, themes=themes)
                        
                        else :
                            # title is not NULL, author and theme are NULL
                            query = "SELECT * FROM book WHERE title = %s;"
                            args = (title,)
                            cur = db.cursor(buffered=True, dictionary=True)
                            cur.execute(query, args)
                            books = cur.fetchall()
                            cur.close()
                            
                            reviews = []
                            for res2 in books:
                                ISBN = res2['ISBN']
                                query = "SELECT * FROM review WHERE ISBN = %s;"
                                args = (ISBN,)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                reviews = reviews + cur.fetchall()
                                cur.close()

                            themes = []
                            for x in books:
                                query = "SELECT * FROM theme WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                themes = themes + cur.fetchall()
                                cur.close()
                            flash("Found the book(s) you requested.")
                            return render_template('results.html', books=books, reviews=reviews, current=current, themes=themes)
                
            if theme != '':
                if author != '':
                    query = "SELECT * FROM book WHERE author = %s;"
                    cur = db.cursor(buffered=True, dictionary=True)
                    args = (author,)
                    cur.execute(query, args)
                    book = cur.fetchall()
                    cur.close()
                    if len(book) == 0:
                        flash("No book with the author you provided exists.")
                        return redirect(url_for('search'))
                    books = []
                    for x in book:
                        query = "SELECT * FROM theme WHERE ISBN = %s AND theme_name = %s;"
                        args = (x['ISBN'], theme)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        res = cur.fetchall()
                        if len(res) == 0:
                            continue
                        else :
                            curr = db.cursor(buffered=True, dictionary=True)
                            query = "SELECT * FROM book WHERE ISBN = %s;"
                            args = (x['ISBN'],)
                            curr.execute(query, args)
                            books = books + curr.fetchall()
                            curr.close()
                        cur.close()

                    if len(books) == 0:
                        flash("No book with all the parameters you specified exists.")
                        return redirect(url_for('search'))
                            
                    reviews = []
                    for x in books:
                        query = "SELECT * FROM review WHERE ISBN = %s;"
                        args = (x['ISBN'],)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        reviews = reviews + cur.fetchall()
                        cur.close()
                    
                    themes = []
                    for x in books:
                        query = "SELECT * FROM theme WHERE ISBN = %s;"
                        args = (x['ISBN'],)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        themes = themes + cur.fetchall()
                        cur.close()

                    flash("Success")
                    return render_template("results.html", books=books, reviews=reviews, current=current, themes=themes)
                else :
                    query = "SELECT * FROM theme WHERE theme_name = %s;"
                    args = (theme,)
                    cur = db.cursor(buffered=True, dictionary=True)
                    cur.execute(query, args)
                    res = cur.fetchall()
                    cur.close()
                    if len(res) == 0:
                        flash("No book with the theme you provided exists in our database.")
                        return redirect(url_for('search'))
                    else:
                        query = "SELECT * FROM theme WHERE theme_name = %s;"
                        args = (theme,)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        res2 = cur.fetchall()
                        cur.close()
                        reviews = []
                        books = []
                        themes= []
                        for x in res2:
                            ISBN = x['ISBN']
                            query = "SELECT * FROM review WHERE ISBN = %s;"
                            args = (ISBN,)
                            cur = db.cursor(buffered=True, dictionary=True)
                            cur.execute(query, args)
                            reviews = reviews + cur.fetchall()
                            cur.close()
                            query = "SELECT * FROM book WHERE ISBN = %s;"
                            cur = db.cursor(buffered=True, dictionary=True)
                            cur.execute(query, args)
                            books = books + cur.fetchall()
                            cur.close()
                            query = "SELECT * FROM theme WHERE ISBN = %s;"
                            args = (ISBN,)
                            cur = db.cursor(buffered=True, dictionary=True)
                            cur.execute(query, args)
                            themes = themes + cur.fetchall()
                            cur.close()
                        flash("Found the book(s) you requested.")
                        return render_template('results.html', books=books, reviews=reviews, current=current, themes=themes)

            if author != '':
                query = "SELECT * FROM book WHERE author = %s;"
                args = (author,)
                cur = db.cursor(buffered=True, dictionary=True)
                cur.execute(query, args)
                res = cur.fetchall()
                cur.close()
                if len(res) == 0:
                    flash("No book with the author you provided exists in our database.")
                    return redirect(url_for('search'))
                else:
                    query = "SELECT * FROM book WHERE author = %s;"
                    args = (author,)
                    cur = db.cursor(buffered=True, dictionary=True)
                    cur.execute(query, args)
                    res2 = cur.fetchall()
                    cur.close()
                    themes = []
                    reviews = []
                    for x in res2:
                        ISBN = x['ISBN']
                        query = "SELECT * FROM review WHERE ISBN = %s;"
                        args = (ISBN,)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        rev = cur.fetchall()
                        cur.close()
                        query = "SELECT * FROM theme WHERE ISBN = %s;"
                        args = (ISBN,)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        th =cur.fetchall()
                        cur.close()
                        themes = themes + th
                        reviews = reviews + rev
                    flash("Found the book(s) you requested.")
                    return render_template('results.html', books=res, reviews=reviews, current=current, themes=themes)
            
        if session['husername'] is not None and copies != '':
            if not checkInt(copies) or copies <= '0':
                flash("Copies must be positive integer!")
                return redirect(url_for('search'))


            query = "SELECT * FROM book WHERE copies = %s;"
            args = (copies,)
            cur = db.cursor(buffered=True, dictionary=True)
            cur.execute(query, args)
            res = cur.fetchall()
            cur.close()
            if len(res) == 0:
                flash("No book with the copies you provided exists in our database.")
                return redirect(url_for('search'))
            

            if title != '':
                query = "SELECT * FROM book WHERE title = %s AND copies = %s;"
                args = (title, copies)
                cur = db.cursor(buffered=True, dictionary=True)
                cur.execute(query, args)
                res = cur.fetchall()
                cur.close()
                if len(res) == 0:
                    flash("No book with the title and copies you provided exists in our database.")
                    return redirect(url_for('search'))
                else:
                    if theme != '':
                        if author != '':
                            # title author and theme are not NULL
                            books = []
                            query = "SELECT * FROM book WHERE title = %s AND author = %s AND copies = %s;"
                            cur = db.cursor(buffered=True, dictionary=True)
                            args = (title, author, copies)
                            cur.execute(query, args)
                            book = cur.fetchall()
                            cur.close()
                            if len(book) == 0:
                                flash("No book with the title, copies author you provided exists.")
                                return redirect(url_for('search'))

                            for b in book:
                                isbn = b['ISBN']
                                query = "SELECT * FROM theme WHERE ISBN = %s AND theme_name = %s;"
                                cur = db.cursor(buffered=True, dictionary=True)
                                args = (isbn, theme)
                                cur.execute(query, args)
                                ans = cur.fetchall()
                                if len(ans) == 0:
                                    continue
                                else :
                                    curr = db.cursor(buffered=True, dictionary=True)
                                    query = "SELECT * FROM book WHERE ISBN = %s;"
                                    args = (isbn,)
                                    curr.execute(query, args)
                                    books = books + curr.fetchall()
                                    curr.close()
                                cur.close()
                            
                            if len(books) == 0:
                                flash("No book with all the parameters you specified exists.")
                                return redirect(url_for('search'))
                            
                            reviews = []
                            for x in books:
                                query = "SELECT * FROM review WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                reviews = reviews + cur.fetchall()
                                cur.close()
                            
                            themes = []
                            for x in books:
                                query = "SELECT * FROM theme WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                themes = themes + cur.fetchall()
                                cur.close()

                            flash("Found the book(s) you requested!")
                            return render_template("results.html", books=books, reviews=reviews, current=current, themes=themes)
                        else :
                            # title and theme are not NULL, author is NULL
                            books = []
                            query = "SELECT * FROM book WHERE title = %s AND copies = %s;"
                            cur = db.cursor(buffered=True, dictionary=True)
                            args = (title, copies)
                            cur.execute(query, args)
                            book = cur.fetchall()
                            cur.close()
                            if len(book) == 0:
                                flash("No book with the title and copies you provided exists.")
                                return redirect(url_for('search'))
                            

                            for b in book:
                                isbn = b['ISBN']
                                query = "SELECT * FROM theme WHERE ISBN = %s AND theme_name = %s;"
                                cur = db.cursor(buffered=True, dictionary=True)
                                args = (isbn, theme)
                                cur.execute(query, args)
                                ans = cur.fetchall()
                                if len(ans) == 0:
                                    continue
                                else :
                                    curr = db.cursor(buffered=True, dictionary=True)
                                    query = "SELECT * FROM book WHERE ISBN = %s;"
                                    args = (isbn,)
                                    curr.execute(query, args)
                                    books = books + curr.fetchall()
                                    curr.close()
                                cur.close()
                            
                            if len(books) == 0:
                                flash("No book with all the parameters you specified exists.")
                                return redirect(url_for('search'))
                            
                            reviews = []
                            for x in books:
                                query = "SELECT * FROM review WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                reviews = reviews + cur.fetchall()
                                cur.close()

                            themes = []
                            for x in books:
                                query = "SELECT * FROM theme WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                themes = themes + cur.fetchall()
                                cur.close()

                            flash("Success")
                            return render_template("results.html", books=books, reviews=reviews, current=current, themes=themes)
                    else :
                        if author != '':
                            # title and author are not NULL, theme is NULL
                            query = "SELECT * FROM book WHERE title = %s AND author = %s AND copies = %s;"
                            cur = db.cursor(buffered=True, dictionary=True)
                            args = (title, author, copies)
                            cur.execute(query, args)
                            book = cur.fetchall()
                            cur.close()
                            if len(book) == 0:
                                flash("No book with the title, copies author you provided exists.")
                                return redirect(url_for('search'))
                            
                            reviews = []
                            for x in book:
                                query = "SELECT * FROM review WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                reviews = reviews + cur.fetchall()
                                cur.close()

                            themes = []
                            for x in book:
                                query = "SELECT * FROM theme WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                themes = themes + cur.fetchall()
                                cur.close()

                            flash("Success")
                            return render_template("results.html", books=book, reviews=reviews, current=current, themes=themes)
                        
                        else :
                            # title is not NULL, author and theme are NULL
                            query = "SELECT * FROM book WHERE title = %s AND copies = %s;"
                            args = (title, copies)
                            cur = db.cursor(buffered=True, dictionary=True)
                            cur.execute(query, args)
                            books = cur.fetchall()
                            cur.close()
                            
                            reviews = []
                            for res2 in books:
                                ISBN = res2['ISBN']
                                query = "SELECT * FROM review WHERE ISBN = %s;"
                                args = (ISBN,)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                reviews = reviews + cur.fetchall()
                                cur.close()

                            themes = []
                            for x in books:
                                query = "SELECT * FROM theme WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                themes = themes + cur.fetchall()
                                cur.close()
                            flash("Found the book(s) you requested.")
                            return render_template('results.html', books=books, reviews=reviews, current=current, themes=themes)
            
            if theme != '':
                if author != '':
                    query = "SELECT * FROM book WHERE author = %s AND copies = %s;"
                    cur = db.cursor(buffered=True, dictionary=True)
                    args = (author, copies)
                    cur.execute(query, args)
                    book = cur.fetchall()
                    cur.close()
                    if len(book) == 0:
                        flash("No book with the author and copies you provided exists.")
                        return redirect(url_for('search'))
                    books = []
                    for x in book:
                        query = "SELECT * FROM theme WHERE ISBN = %s AND theme_name = %s;"
                        args = (x['ISBN'], theme)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        res = cur.fetchall()
                        if len(res) == 0:
                            continue
                        else :
                            curr = db.cursor(buffered=True, dictionary=True)
                            query = "SELECT * FROM book WHERE ISBN = %s;"
                            args = (x['ISBN'],)
                            curr.execute(query, args)
                            books = books + curr.fetchall()
                            curr.close()
                        cur.close()

                    if len(books) == 0:
                        flash("No book with all the parameters you specified exists.")
                        return redirect(url_for('search'))
                            
                    reviews = []
                    for x in books:
                        query = "SELECT * FROM review WHERE ISBN = %s;"
                        args = (x['ISBN'],)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        reviews = reviews + cur.fetchall()
                        cur.close()
                    
                    themes = []
                    for x in books:
                        query = "SELECT * FROM theme WHERE ISBN = %s;"
                        args = (x['ISBN'],)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        themes = themes + cur.fetchall()
                        cur.close()

                    flash("Success")
                    return render_template("results.html", books=books, reviews=reviews, current=current, themes=themes)
                else :
                    query = "SELECT * FROM theme WHERE theme_name = %s;"
                    args = (theme,)
                    cur = db.cursor(buffered=True, dictionary=True)
                    cur.execute(query, args)
                    res = cur.fetchall()
                    cur.close()
                    if len(res) == 0:
                        flash("No book with the theme and copies you provided exists in our database.")
                        return redirect(url_for('search'))
                    else:
                        query = "SELECT * FROM theme WHERE theme_name = %s;"
                        args = (theme,)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        res2 = cur.fetchall()
                        cur.close()
                        reviews = []
                        books = []
                        themes= []
                        for x in res2:
                            ISBN = x['ISBN']
                            query = "SELECT * FROM review WHERE ISBN = %s;"
                            args = (ISBN,)
                            cur = db.cursor(buffered=True, dictionary=True)
                            cur.execute(query, args)
                            reviews = reviews + cur.fetchall()
                            cur.close()
                            query = "SELECT * FROM book WHERE ISBN = %s and copies = %s;"
                            args = (ISBN, copies)
                            cur = db.cursor(buffered=True, dictionary=True)
                            cur.execute(query, args)
                            books = books + cur.fetchall()
                            cur.close()
                            query = "SELECT * FROM theme WHERE ISBN = %s;"
                            args = (ISBN,)
                            cur = db.cursor(buffered=True, dictionary=True)
                            cur.execute(query, args)
                            themes = themes + cur.fetchall()
                            cur.close()
                        flash("Found the book(s) you requested.")
                        return render_template('results.html', books=books, reviews=reviews, current=current, themes=themes)

            if author != '':
                query = "SELECT * FROM book WHERE author = %s AND copies = %s;"
                args = (author, copies)
                cur = db.cursor(buffered=True, dictionary=True)
                cur.execute(query, args)
                res = cur.fetchall()
                cur.close()
                if len(res) == 0:
                    flash("No book with the author and copies you provided exists in our database.")
                    return redirect(url_for('search'))
                else:
                    query = "SELECT * FROM book WHERE author = %s;"
                    args = (author,)
                    cur = db.cursor(buffered=True, dictionary=True)
                    cur.execute(query, args)
                    res2 = cur.fetchall()
                    cur.close()
                    themes = []
                    reviews = []
                    for x in res2:
                        ISBN = x['ISBN']
                        query = "SELECT * FROM review WHERE ISBN = %s;"
                        args = (ISBN,)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        rev = cur.fetchall()
                        cur.close()
                        query = "SELECT * FROM theme WHERE ISBN = %s;"
                        args = (ISBN,)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        th =cur.fetchall()
                        cur.close()
                        themes = themes + th
                        reviews = reviews + rev
                    flash("Found the book(s) you requested.")
                    return render_template('results.html', books=res, reviews=reviews, current=current, themes=themes)
                
            else :
                query = "SELECT * FROM book WHERE copies = %s;"
                args = (copies,)
                cur = db.cursor(buffered=True, dictionary=True)
                cur.execute(query, args)
                res = cur.fetchall()
                cur.close()
                if len(res) == 0:
                    flash("No book with the copies you provided exists.")
                    return redirect(url_for('search'))
                reviews = []
                themes = []
                for x in res:
                    ISBN = x['ISBN']
                    query = "SELECT * FROM review WHERE ISBN = %s;"
                    args = (ISBN,)
                    cur = db.cursor(buffered=True, dictionary=True)
                    cur.execute(query, args)
                    reviews = reviews + cur.fetchall()
                    cur.close()
                    query = "SELECT * FROM theme WHERE ISBN = %s;"
                    args = (ISBN,)
                    cur = db.cursor(buffered=True, dictionary=True)
                    cur.execute(query, args)
                    themes = themes + cur.fetchall()
                    cur.close()
                flash("Found the book(s) you requested.")
                return render_template('results.html', books=res, reviews=reviews, current=current, themes=themes)
        

        else :
            # copies are not given as argument
            
            if title != '':
                query = "SELECT * FROM book WHERE title = %s;"
                args = (title,)
                cur = db.cursor(buffered=True, dictionary=True)
                cur.execute(query, args)
                res = cur.fetchall()
                cur.close()
                if len(res) == 0:
                    flash("No book with the title you provided exists in our database.")
                    return redirect(url_for('search'))
                else:
                    if theme != '':
                        if author != '':
                            # title author and theme are not NULL
                            books = []
                            query = "SELECT * FROM book WHERE title = %s AND author = %s;"
                            cur = db.cursor(buffered=True, dictionary=True)
                            args = (title, author)
                            cur.execute(query, args)
                            book = cur.fetchall()
                            cur.close()
                            if len(book) == 0:
                                flash("No book with the title and author you provided exists.")
                                return redirect(url_for('search'))

                            for b in book:
                                isbn = b['ISBN']
                                query = "SELECT * FROM theme WHERE ISBN = %s AND theme_name = %s;"
                                cur = db.cursor(buffered=True, dictionary=True)
                                args = (isbn, theme)
                                cur.execute(query, args)
                                ans = cur.fetchall()
                                if len(ans) == 0:
                                    continue
                                else :
                                    curr = db.cursor(buffered=True, dictionary=True)
                                    query = "SELECT * FROM book WHERE ISBN = %s;"
                                    args = (isbn,)
                                    curr.execute(query, args)
                                    books = books + curr.fetchall()
                                    curr.close()
                                cur.close()
                            
                            if len(books) == 0:
                                flash("No book with all the parameters you specified exists.")
                                return redirect(url_for('search'))
                            
                            reviews = []
                            for x in books:
                                query = "SELECT * FROM review WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                reviews = reviews + cur.fetchall()
                                cur.close()
                            
                            themes = []
                            for x in books:
                                query = "SELECT * FROM theme WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                themes = themes + cur.fetchall()
                                cur.close()

                            flash("Success!")
                            return render_template("results.html", books=books, reviews=reviews, current=current, themes=themes)
                        else :
                            # title and theme are not NULL, author is NULL
                            books = []
                            query = "SELECT * FROM book WHERE title = %s;"
                            cur = db.cursor(buffered=True, dictionary=True)
                            args = (title,)
                            cur.execute(query, args)
                            book = cur.fetchall()
                            cur.close()
                            if len(book) == 0:
                                flash("No book with the title you provided exists.")
                                return redirect(url_for('search'))
                            

                            for b in book:
                                isbn = b['ISBN']
                                query = "SELECT * FROM theme WHERE ISBN = %s AND theme_name = %s;"
                                cur = db.cursor(buffered=True, dictionary=True)
                                args = (isbn, theme)
                                cur.execute(query, args)
                                ans = cur.fetchall()
                                if len(ans) == 0:
                                    continue
                                else :
                                    curr = db.cursor(buffered=True, dictionary=True)
                                    query = "SELECT * FROM book WHERE ISBN = %s;"
                                    args = (isbn,)
                                    curr.execute(query, args)
                                    books = books + curr.fetchall()
                                    curr.close()
                                cur.close()
                            
                            if len(books) == 0:
                                flash("No book with all the parameters you specified exists.")
                                return redirect(url_for('search'))
                            
                            reviews = []
                            for x in books:
                                query = "SELECT * FROM review WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                reviews = reviews + cur.fetchall()
                                cur.close()

                            themes = []
                            for x in books:
                                query = "SELECT * FROM theme WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                themes = themes + cur.fetchall()
                                cur.close()

                            flash("Success")
                            return render_template("results.html", books=books, reviews=reviews, current=current, themes=themes)
                    else :
                        if author != '':
                            # title and author are not NULL, theme is NULL
                            query = "SELECT * FROM book WHERE title = %s AND author = %s;"
                            cur = db.cursor(buffered=True, dictionary=True)
                            args = (title, author)
                            cur.execute(query, args)
                            book = cur.fetchall()
                            cur.close()
                            if len(book) == 0:
                                flash("No book with the title and author you provided exists.")
                                return redirect(url_for('search'))
                            
                            reviews = []
                            for x in book:
                                query = "SELECT * FROM review WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                reviews = reviews + cur.fetchall()
                                cur.close()

                            themes = []
                            for x in book:
                                query = "SELECT * FROM theme WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                themes = themes + cur.fetchall()
                                cur.close()

                            flash("Success")
                            return render_template("results.html", books=book, reviews=reviews, current=current, themes=themes)
                        
                        else :
                            # title is not NULL, author and theme are NULL
                            query = "SELECT * FROM book WHERE title = %s;"
                            args = (title,)
                            cur = db.cursor(buffered=True, dictionary=True)
                            cur.execute(query, args)
                            books = cur.fetchall()
                            cur.close()
                            
                            reviews = []
                            for res2 in books:
                                ISBN = res2['ISBN']
                                query = "SELECT * FROM review WHERE ISBN = %s;"
                                args = (ISBN,)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                reviews = reviews + cur.fetchall()
                                cur.close()

                            themes = []
                            for x in books:
                                query = "SELECT * FROM theme WHERE ISBN = %s;"
                                args = (x['ISBN'],)
                                cur = db.cursor(buffered=True, dictionary=True)
                                cur.execute(query, args)
                                themes = themes + cur.fetchall()
                                cur.close()
                            flash("Found the book(s) you requested.")
                            return render_template('results.html', books=books, reviews=reviews, current=current, themes=themes)
                
            if theme != '':
                if author != '':
                    query = "SELECT * FROM book WHERE author = %s;"
                    cur = db.cursor(buffered=True, dictionary=True)
                    args = (author,)
                    cur.execute(query, args)
                    book = cur.fetchall()
                    cur.close()
                    if len(book) == 0:
                        flash("No book with the author you provided exists.")
                        return redirect(url_for('search'))
                    books = []
                    for x in book:
                        query = "SELECT * FROM theme WHERE ISBN = %s AND theme_name = %s;"
                        args = (x['ISBN'], theme)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        res = cur.fetchall()
                        if len(res) == 0:
                            continue
                        else :
                            curr = db.cursor(buffered=True, dictionary=True)
                            query = "SELECT * FROM book WHERE ISBN = %s;"
                            args = (x['ISBN'],)
                            curr.execute(query, args)
                            books = books + curr.fetchall()
                            curr.close()
                        cur.close()

                    if len(books) == 0:
                        flash("No book with all the parameters you specified exists.")
                        return redirect(url_for('search'))
                            
                    reviews = []
                    for x in books:
                        query = "SELECT * FROM review WHERE ISBN = %s;"
                        args = (x['ISBN'],)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        reviews = reviews + cur.fetchall()
                        cur.close()
                    
                    themes = []
                    for x in books:
                        query = "SELECT * FROM theme WHERE ISBN = %s;"
                        args = (x['ISBN'],)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        themes = themes + cur.fetchall()
                        cur.close()

                    flash("Success")
                    return render_template("results.html", books=books, reviews=reviews, current=current, themes=themes)
                else :
                    query = "SELECT * FROM theme WHERE theme_name = %s;"
                    args = (theme,)
                    cur = db.cursor(buffered=True, dictionary=True)
                    cur.execute(query, args)
                    res = cur.fetchall()
                    cur.close()
                    if len(res) == 0:
                        flash("No book with the theme you provided exists in our database.")
                        return redirect(url_for('search'))
                    else:
                        query = "SELECT * FROM theme WHERE theme_name = %s;"
                        args = (theme,)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        res2 = cur.fetchall()
                        cur.close()
                        reviews = []
                        books = []
                        themes= []
                        for x in res2:
                            ISBN = x['ISBN']
                            query = "SELECT * FROM review WHERE ISBN = %s;"
                            args = (ISBN,)
                            cur = db.cursor(buffered=True, dictionary=True)
                            cur.execute(query, args)
                            reviews = reviews + cur.fetchall()
                            cur.close()
                            query = "SELECT * FROM book WHERE ISBN = %s;"
                            cur = db.cursor(buffered=True, dictionary=True)
                            cur.execute(query, args)
                            books = books + cur.fetchall()
                            cur.close()
                            query = "SELECT * FROM theme WHERE ISBN = %s;"
                            args = (ISBN,)
                            cur = db.cursor(buffered=True, dictionary=True)
                            cur.execute(query, args)
                            themes = themes + cur.fetchall()
                            cur.close()
                        flash("Found the book(s) you requested.")
                        return render_template('results.html', books=books, reviews=reviews, current=current, themes=themes)

            if author != '':
                query = "SELECT * FROM book WHERE author = %s;"
                args = (author,)
                cur = db.cursor(buffered=True, dictionary=True)
                cur.execute(query, args)
                res = cur.fetchall()
                cur.close()
                if len(res) == 0:
                    flash("No book with the author you provided exists in our database.")
                    return redirect(url_for('search'))
                else:
                    query = "SELECT * FROM book WHERE author = %s;"
                    args = (author,)
                    cur = db.cursor(buffered=True, dictionary=True)
                    cur.execute(query, args)
                    res2 = cur.fetchall()
                    cur.close()
                    themes = []
                    reviews = []
                    for x in res2:
                        ISBN = x['ISBN']
                        query = "SELECT * FROM review WHERE ISBN = %s;"
                        args = (ISBN,)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        rev = cur.fetchall()
                        cur.close()
                        query = "SELECT * FROM theme WHERE ISBN = %s;"
                        args = (ISBN,)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        th =cur.fetchall()
                        cur.close()
                        themes = themes + th
                        reviews = reviews + rev
                    flash("Found the book(s) you requested.")
                    return render_template('results.html', books=res, reviews=reviews, current=current, themes=themes)
        
    return render_template('search.html')

@app.route("/<string:ISBN>/make_reservation", methods=('GET', 'POST'))
@login_required
def make_reservation(ISBN):
    update_reservations()
    if request.method == 'POST':
        # find reservation_id of last and add one to find current reservation_id
        query = "SELECT reservation_id FROM reservations ORDER BY reservation_id DESC LIMIT 1;"
        cur = db.cursor()
        cur.execute(query)
        res = cur.fetchone()
        cur.close()
        if res is None:
            id = 1
        else:
            id = res[0] + 1

        # check that the user is eligible to make the reservation
        # find how many active reservations this user has
        username = session['username']
        query = "SELECT * FROM reservations WHERE username = %s AND is_over = 'F';"
        args = (username,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        res = cur.fetchall()
        reserv = len(res)

        # don't let user make 2 reservations about the same book
        query = "SELECT * FROM reservations WHERE username = %s AND is_over = 'F' AND ISBN = %s;"
        args = (username, ISBN)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        curr_reservations = cur.fetchall()
        check = len(curr_reservations)

        if check == 1:
            flash("You cannot make more than one reservation about this book, try a different one.")
            return redirect(url_for('books'))

        # find out if this user is a student or not        
        query = "SELECT is_student FROM user WHERE username = %s;"
        args = (username,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        is_student = cur.fetchone()

        if is_student['is_student'] == 'T' and reserv == 2:
            flash("You cannot make more reservations this week.")
            return redirect(url_for('view_reservations'))
        if is_student['is_student'] == 'F' and reserv == 1:
            flash("You cannot make more reservations this week.")
            return redirect(url_for('view_reservations'))
        
        # find out if this user has due returns or wants to reserve a book he has currently borrowed
        query = "SELECT * FROM now_borrowed WHERE username = %s AND is_returned = 'F';"
        args = (username,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        res = cur.fetchall()
        current_time = datetime.datetime.now().replace(microsecond=0)
        for x in res:
            if x['start_d'] + datetime.timedelta(days=7) < current_time:
                flash("You have pending books to return, cannot make reservation.")
                return redirect(url_for('books'))
            if x['ISBN'] == ISBN:
                flash("Cannot make reservation for a book you have currently borrowed.")
                return redirect(url_for('books'))
            
        # find out if there are copies currently available from this book, thus mark the reservation as active
        query = "SELECT current FROM currently_available WHERE ISBN = %s;"
        args = (ISBN,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        av = cur.fetchone()
        cur.close()
        currently_available = av['current']

        if currently_available > 0:
            is_active = 'T'
        elif currently_available == 0:
            is_active = 'F'

        # make the reservation
        if is_active == 'T':
            query = "INSERT INTO reservations(reservation_id, ISBN, tdate, username, rdate, is_active, is_over) VALUES (%s, %s, %s, %s, %s, %s, 'F');"
            tdate = datetime.datetime.now().replace(microsecond=0)
            rdate =  tdate + datetime.timedelta(days=7)
            args = (id, ISBN, tdate, username, rdate, is_active)
            cur = db.cursor()
            cur.execute(query, args)
            db.commit()
            cur.close()
            flash("Your reservation was made successfully, pick up the book from the library.")
            update_table()

            return redirect(url_for('books'))
        elif is_active == 'F':
            # find when this reservation can be made
            query = "SELECT * FROM now_borrowed WHERE ISBN = %s AND is_returned = 'F' ORDER BY transaction_id DESC;"
            args = (ISBN,)
            cur = db.cursor(buffered=True, dictionary=True)
            cur.execute(query, args)
            borrowed = cur.fetchall()
            query = "SELECT * FROM reservations WHERE ISBN = %s AND is_over = 'F' ORDER BY reservation_id DESC;"
            args = (ISBN,)
            cur = db.cursor(buffered=True, dictionary=True)
            cur.execute(query, args)
            reserved = cur.fetchall()
            cur.close()
            if len(reserved) < len(borrowed):
                t = 0
                for o in borrowed:
                    if t == len(borrowed) - len(reserved):
                        break
                    t = t + 1
                tdate = o['return_date']
                rdate = tdate + datetime.timedelta(days=7)
                query = "INSERT INTO reservations(reservation_id, ISBN, tdate, username, rdate, is_active, is_over) VALUES (%s, %s, %s, %s, %s, %s, 'F');"
                args = (id, ISBN, tdate, username, rdate, is_active)
                cur = db.cursor()
                cur.execute(query, args)
                db.commit()
                cur.close()
                flash("No copies are currently available, but your reservation was made for the projected return of the copies. Check reservations tab for more.")
                update_table()
                return redirect(url_for('books'))
            else:
                query = "SELECT * FROM reservations WHERE ISBN = %s AND is_over = 'F' ORDER BY reservation_id DESC LIMIT 1;"
                args = (ISBN,)
                cur = db.cursor(buffered=True, dictionary=True)
                cur.execute(query, args)
                reserved = cur.fetchone()
                cur.close()
                tdate = reserved['rdate']
                rdate = tdate + datetime.timedelta(days=7)
                query = "INSERT INTO reservations(reservation_id, ISBN, tdate, username, rdate, is_active, is_over) VALUES (%s, %s, %s, %s, %s, %s, 'F');"
                args = (id, ISBN, tdate, username, rdate, is_active)
                cur = db.cursor()
                cur.execute(query, args)
                db.commit()
                cur.close()
                flash("No copies are currently available, but your reservation was made for the projected return of the copies. Check reservations tab for more.")
                update_table()
                return redirect(url_for('books'))

        update_table()

        return redirect(url_for('books'))
    

    return render_template('books.html')

@app.route("/view_reservations")
@login_required
def view_reservations():
    update_reservations()
    username = session['username']
    query = 'SELECT * FROM reservations WHERE username = %s;'
    args = (username,)
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query, args)
    reservations = cur.fetchall()
    cur.close()
    return render_template("view_reservations.html", reservations=reservations)

@app.route("/<int:reservation_id>/rdelete", methods=('GET', 'POST'))
@login_required
def rdelete(reservation_id):
    update_reservations()
    if request.method == 'POST':
        query = "UPDATE reservations SET is_over = 'T' WHERE reservation_id = %s;"
        args = (reservation_id,)
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()
        update_reservations()
        update_table()
        flash("Reservation was cancelled successfully.")
        return redirect(url_for('view_reservations'))
    return render_template('books.html')

@app.route("/<string:ISBN>/vreservations")
@handler_required
def vreservations(ISBN):
    update_reservations()
    query = "SELECT * FROM reservations WHERE ISBN = %s;"
    args = (ISBN,)
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query, args)
    reservations = cur.fetchall()
    cur.close()
    return render_template('vreservations.html', reservations=reservations)

@app.route("/<int:reservation_id>/make_borrow", methods=('POST', 'GET'))
@handler_required
def make_borrow(reservation_id):
    update_reservations()
    if request.method == 'POST':
        query = "SELECT * FROM reservations WHERE reservation_id = %s;"
        args = (reservation_id,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        res = cur.fetchone()
        cur.close()

        # find if the user is eligible to borrow this book
        username = res['username']
        ISBN = res['ISBN']
        query = "SELECT * FROM now_borrowed WHERE username = %s AND is_returned = 'F';"
        args = (username,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        borr = cur.fetchall()
        cur.close()
        active_borrowings = len(borr)

        query = "SELECT * FROM user WHERE username = %s;"
        args = (username,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        st = cur.fetchone()
        cur.close()
        if st['is_student'] == 'F':
            is_student = 'F'
        elif st['is_student'] == 'T':
            is_student = 'T'

        if is_student == 'T' and active_borrowings == 2:
            flash("This student has already borrowed 2 books this week, cannot borrow more until one is returned.")
            return redirect(url_for('books'))
        if is_student == 'F' and active_borrowings == 1:
            flash("This teacher has already borrowed 1 book this week, cannot borrow more until one is returned.")
            return redirect(url_for('books'))
        
        # find out if this user has due returns or wants to reserve a book he has currently borrowed
        query = "SELECT * FROM now_borrowed WHERE username = %s AND is_returned = 'F';"
        args = (username,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        res = cur.fetchall()
        cur.close()
        current_time = datetime.datetime.now().replace(microsecond=0)
        for x in res:
            if x['return_date'] < current_time:
                flash("This user has out_of date return, cannot register a borrow.")
                return redirect(url_for('books'))
            if x['ISBN'] == ISBN:
                flash("This user has currently borrowed this book.")
                return redirect(url_for('books'))
            
        # find out if there are copies available
        query = "SELECT * FROM reservations WHERE username = %s AND is_active = 'T' AND ISBN = %s;"
        args = (username, ISBN)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        res2 = cur.fetchone()
        cur.close()
        this = 'T'
        if res2 is None or res2['is_active'] == 'F':
            this = 'F'
        query = "SELECT * FROM currently_available WHERE ISBN = %s;"
        args = (ISBN,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        res2 = cur.fetchone()
        cur.close()
        if res2['current'] == 0 and this == 'F':
            flash("No copies of this book are available, thus can't register a borrowing.")
            return redirect(url_for('books'))

        # find transaction id in borrow table
        query = "SELECT transaction_id FROM now_borrowed ORDER BY transaction_id DESC LIMIT 1;"
        cur = db.cursor()
        cur.execute(query)
        x = cur.fetchone()
        if x is None:
            id = 1
        else:
            id = x[0] + 1
        tdate = datetime.datetime.now().replace(microsecond=0)
        rdate =  tdate + datetime.timedelta(days=7)
        query = "UPDATE reservations SET is_active = 'F', is_over = 'T' WHERE reservation_id = %s;"
        args = (reservation_id,)
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()
        query = "INSERT INTO now_borrowed(transaction_id, ISBN, username, start_d, is_returned, return_date, school_id) VALUES (%s, %s, %s, %s, 'F', %s, %s);"
        args = (id, ISBN, username, tdate, rdate, session['school_id'])
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()

        update_table()

        flash("Borrowing was successfully registered.")
        return redirect(url_for('books'))
    
    return redirect(url_for('books'))

@app.route("/register_borrow", methods=('GET', 'POST'))
@handler_required
def register_borrow():
    update_reservations()
    if request.method == 'POST':
        ISBN =  request.form['ISBN']
        username = request.form['user']

        # check that the borrowing is made for a book of this handler's school
        query = "SELECT school_id FROM book WHERE ISBN = %s"
        args = (ISBN,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        res = cur.fetchone()
        cur.close()
        if (res['school_id'] != session['school_id']):
            flash("Can't register the borrowing of a book that is not in your school.")
            return (redirect(url_for('books')))

        # check that the user is eligible for the borrowing
        query = "SELECT * FROM now_borrowed WHERE username = %s;"
        args = (username,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        res = cur.fetchall()
        reserv = len(res)

        query = "SELECT is_student FROM user WHERE username = %s;"
        args = (username,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        is_student = cur.fetchone()

        if is_student['is_student'] == 'T' and reserv == 2:
            flash("This user has already borrowed 2 books this week.")
            return redirect(url_for('view_reservations'))
        if is_student['is_student'] == 'F' and reserv == 1:
            flash("This teacher has already borrowed 1 book this week.")
            return redirect(url_for('view_reservations'))
        
        query = "SELECT * FROM now_borrowed WHERE username = %s;"
        args = (username,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        res = cur.fetchall()
        cur.close()
        current_time = datetime.datetime.now().replace(microsecond=0)
        for x in res:
            if x['return_date'] < current_time:
                flash("This user has pending books to return.")
                return redirect(url_for('books'))
            if x['ISBN'] == ISBN:
                flash("This user has already borrowed this book.")
                return redirect(url_for('books'))
            
        # find transaction id in borrow table
        query = "SELECT transaction_id FROM now_borrowed ORDER BY transaction_id DESC LIMIT 1;"
        cur = db.cursor()
        cur.execute(query)
        x = cur.fetchone()
        cur.close()
        if x is None:
            id = 1
        else:
            id = x[0] + 1

        # make the borrowing
        query = "INSERT INTO now_borrowed(transaction_id, ISBN, username, start_d, is_returned, return_date, school_id) VALUES (%s, %s, %s, %s, 'F', %s, %s);"
        tdate = datetime.datetime.now().replace(microsecond=0)
        rdate =  tdate + datetime.timedelta(days=7)
        args = (id, ISBN, username, tdate, rdate, session['school_id'])
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()

        update_table()

        flash("Successfully registered the borrowing.")
        return redirect(url_for('books'))
    
    return render_template('register_borrow.html')

@app.route("/register_return", methods=('GET', 'POST'))
@handler_required
def register_return():
    update_reservations()
    if request.method == 'POST':
        
        ISBN = request.form['ISBN']
        # check that the borrowing is made for a book of this handler's school
        query = "SELECT school_id FROM book WHERE ISBN = %s"
        args = (ISBN,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        res = cur.fetchone()
        cur.close()
        if (res != session['school_id']):
            flash("Can't register the return of a book that is not in your school.")
            return (redirect(url_for('books')))

        #check for valid input
        username = request.form['user']
        args = (username, ISBN)
        query = "SELECT * FROM now_borrowed WHERE username = %s AND ISBN = %s;"
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        res = cur.fetchall()
        cur.close()

        if len(res) == 0:
            flash("You made a spelling mistake, no such active borrowing exists.")
            return redirect(url_for('books'))
        
        query = "UPDATE now_borrowed SET is_returned = 'T' WHERE username = %s AND ISBN = %s;"
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()

        update_table()
        flash("Successfully registered the return of this book.")
        return redirect(url_for('books'))
    
    return render_template('register_return.html')

@app.route("/view_borrowings")
@handler_required
def view_borrowings():
    update_reservations()
    query = "SELECT * FROM now_borrowed WHERE school_id = %s;"
    cur = db.cursor(buffered=True, dictionary=True)
    args = (session['school_id'],)
    cur.execute(query, args)
    borrowings = cur.fetchall()
    cur.close()
    return render_template('view_borrowings.html', borrowings=borrowings)

@app.route("/<int:transaction_id>/make_return", methods=('GET', 'POST'))
@handler_required
def make_return(transaction_id):
    update_reservations()
    if request.method == 'POST':
        query = "UPDATE now_borrowed SET is_returned = 'T' WHERE transaction_id = %s;"
        args = (transaction_id,)
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()
        update_table()
        flash("Successfully registered the return.")
        return redirect(url_for('books'))
    
    return render_template("books.html")

@app.route("/search_user", methods=('GET', 'POST'))
@handler_required
def search_user():
    update_reservations()
    if request.method == 'POST':
        username = request.form['user']
        args = (username, session['school_id'])
        # only see users from the same school
        query = "SELECT * FROM user WHERE username = %s AND school_id = %s;"
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        user_info = cur.fetchone()
        cur.close()
        if user_info is None:
            flash("No such user exists.")
            return redirect(url_for('books'))
        args = (username,)
        query = "SELECT * FROM now_borrowed WHERE username = %s;"
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        borrowings = cur.fetchall()
        cur.close()
        query = "SELECT * FROM reservations WHERE username = %s;"
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        reservations = cur.fetchall()
        cur.close()
        return render_template('user_results.html', info = user_info, borrowings = borrowings, reservations = reservations)
    
    return render_template('search_user.html')

@app.route("/main_page")
@login_required
def main_page():
    update_reservations()
    return render_template("main_page.html")

@app.route("/borrowing_history")
@login_required
def borrowing_history():
    query = "SELECT * FROM now_borrowed WHERE username = %s;"
    args = (session['username'],)
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query, args)
    history = cur.fetchall()
    cur.close()
    return render_template("borrowing_history.html", history=history)

@app.route("/overdue_returns", methods=('GET', 'POST'))
@handler_required
def overdue_returns():
    if request.method == 'POST':
        
        ctime = datetime.datetime.now().replace(microsecond=0)
        ans = []

        if request.form['name'] != '':
            if request.form['lastname'] != '':
                # see if user exists
                query = "SELECT * FROM person WHERE first_name = %s AND last_name = %s;"
                args = (request.form['name'], request.form['lastname'])
                cur = db.cursor(buffered=True, dictionary=True)
                cur.execute(query, args)
                persons = cur.fetchall()
                cur.close()
                if len(persons) == 0:
                    flash("No such user exists.")
                    return redirect(url_for('overdue_returns'))
                
                if request.form['days'] != '':
                    if request.form['days'] < '0':
                        flash("Days must be positive.")
                        return redirect(url_for('overdue_returns'))
                    
                    if not checkInt(request.form['days']):
                        flash("Days must be integers!")
                        return redirect(url_for('overdue_returns'))
                    
                    borrowings = []
                    for p in persons:
                        query = "SELECT username FROM user WHERE person_id = %s"
                        args = (p['person_id'],)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        user = cur.fetchone()
                        cur.close()
                        query = "SELECT * FROM now_borrowed WHERE username = %s AND is_returned = 'F' AND start_d < %s"
                        try :
                            time = ctime - datetime.timedelta(days=7 + int(request.form['days']))
                        except Exception as e:
                            flash(e)
                            return redirect(url_for('overdue_returns'))
                        args = (user['username'], time)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        res = cur.fetchall()
                        for x in res:
                            time = x['return_date']
                            if time is None or time == '':
                                timediff = ctime - x['start_d'] - datetime.timedelta(days=7)
                                x['return_date'] = timediff
                        borrowings = res + borrowings
                        cur.close()
                    if len(borrowings) == 0:
                        flash("No results to your query.")
                    return render_template('overdue_return_results.html', borrowings=borrowings)


                else :
                    borrowings = []
                    for p in persons:
                        query = "SELECT username FROM user WHERE person_id = %s"
                        args = (p['person_id'],)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        user = cur.fetchone()
                        cur.close()
                        query = "SELECT * FROM now_borrowed WHERE username = %s AND is_returned = 'F' AND start_d < %s"
                        time = ctime - datetime.timedelta(days=7)
                        args = (user['username'], time)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        res = cur.fetchall()
                        for x in res:
                            time = x['return_date']
                            if time is None or time == '':
                                timediff = ctime - x['start_d'] - datetime.timedelta(days=7)
                                x['return_date'] = timediff
                        borrowings = res + borrowings
                        cur.close()
                    if len(borrowings) == 0:
                        flash("No results to your query.")
                    return render_template('overdue_return_results.html', borrowings=borrowings)
            else :
                if request.form['days'] != '':
                    if request.form['days'] < '0':
                        flash("Days must be positive.")
                        return redirect(url_for('overdue_returns'))
                    
                    if not checkInt(request.form['days']):
                        flash("Days must be integers!")
                        return redirect(url_for('overdue_returns'))
                    
                    query = "SELECT * FROM person WHERE first_name = %s;"
                    args = (request.form['name'],)
                    cur = db.cursor(buffered=True, dictionary=True)
                    cur.execute(query, args)
                    persons = cur.fetchall()
                    cur.close()
                    if len(persons) == 0:
                        flash("No such user exists.")
                        return redirect(url_for('overdue_returns'))
                    borrowings = []
                    for p in persons:
                        query = "SELECT username FROM user WHERE person_id = %s"
                        args = (p['person_id'],)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        user = cur.fetchone()
                        cur.close()
                        query = "SELECT * FROM now_borrowed WHERE username = %s AND is_returned = 'F' AND start_d < %s"
                        try :
                            time = ctime - datetime.timedelta(days=7 + int(request.form['days']))
                        except Exception as e:
                            flash(e)
                            return redirect(url_for('overdue_returns'))
                        args = (user['username'], time)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        res = cur.fetchall()
                        for x in res:
                            time = x['return_date']
                            if time is None or time == '':
                                timediff = ctime - x['start_d'] - datetime.timedelta(days=7)
                                x['return_date'] = timediff
                        borrowings = res + borrowings
                        cur.close()
                    if len(borrowings) == 0:
                        flash("No results to your query.")
                    return render_template('overdue_return_results.html', borrowings=borrowings)
                
                else :
                    query = "SELECT person_id FROM person WHERE first_name = %s;"
                    cur = db.cursor(buffered=True, dictionary=True)
                    args = (request.form['name'],)
                    cur.execute(query, args)
                    ids = cur.fetchall()
                    cur.close()
                    persons = []
                    for id in ids:
                        persons.append(id['person_id'])

                    usernames = []
                    for i in persons:
                        query = "SELECT username FROM user WHERE person_id = %s;"
                        args = (i,)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        res = cur.fetchone()
                        usernames.append(res['username'])
                        cur.close()

                    for user in usernames:
                        query = "SELECT * FROM now_borrowed WHERE username = %s AND is_returned = 'F' AND start_d < %s;"
                        time = ctime - datetime.timedelta(days=7)
                        args = (user, time)
                        cur = db.cursor(buffered=True, dictionary=True)
                        cur.execute(query, args)
                        res = cur.fetchall()
                        for x in res:
                            time = x['return_date']
                            if time is None or time == '':
                                timediff = ctime - x['start_d'] - datetime.timedelta(days=7)
                                x['return_date'] = timediff
                        ans = ans + res
                        cur.close()
                    
                    if len(ans) == 0:
                        flash("No overdue returns.")


                    return render_template('overdue_return_results.html', borrowings=ans)
        
        if request.form['lastname'] != '':
            if request.form['days'] != '':
                if request.form['days'] < '0':
                    flash("Days must be positive integer")
                    return redirect(url_for('overdue_returns'))
                
                if not checkInt(request.form['days']):
                    flash("Days must be integers!")
                    return redirect(url_for('overdue_returns'))
                
                query = "SELECT person_id FROM person WHERE last_name = %s;"
                cur = db.cursor(buffered=True, dictionary=True)
                args = (request.form['lastname'],)
                cur.execute(query, args)
                ids = cur.fetchall()
                cur.close()
                persons = []
                for id in ids:
                    persons.append(id['person_id'])

                usernames = []
                for i in persons:
                    query = "SELECT username FROM user WHERE person_id = %s;"
                    args = (i,)
                    cur = db.cursor(buffered=True, dictionary=True)
                    cur.execute(query, args)
                    res = cur.fetchone()
                    usernames.append(res['username'])
                    cur.close()

                for user in usernames:
                    query = "SELECT * FROM now_borrowed WHERE username = %s AND is_returned = 'F' AND start_d < %s;"
                    try :
                        time = ctime - datetime.timedelta(days=7 + int(request.form['days']))
                    except Exception as e:
                        flash(e)
                        return redirect(url_for('overdue_returns'))
                    args = (user, time)
                    cur = db.cursor(buffered=True, dictionary=True)
                    cur.execute(query, args)
                    res = cur.fetchall()
                    for x in res:
                        time = x['return_date']
                        if time is None or time == '':
                            timediff = ctime - x['start_d'] - datetime.timedelta(days=7)
                            x['return_date'] = timediff
                    ans = ans + res
                    cur.close()

                return render_template('overdue_return_results.html', borrowings=ans)
            
            else :

                query = "SELECT person_id FROM person WHERE last_name = %s;"
                cur = db.cursor(buffered=True, dictionary=True)
                args = (request.form['lastname'],)
                cur.execute(query, args)
                ids = cur.fetchall()
                cur.close()
                persons = []
                for id in ids:
                    persons.append(id['person_id'])

                usernames = []
                for i in persons:
                    query = "SELECT username FROM user WHERE person_id = %s;"
                    args = (i,)
                    cur = db.cursor(buffered=True, dictionary=True)
                    cur.execute(query, args)
                    res = cur.fetchone()
                    usernames.append(res['username'])
                    cur.close()

                for user in usernames:
                    query = "SELECT * FROM now_borrowed WHERE username = %s AND is_returned = 'F' AND start_d < %s;"
                    time = ctime - datetime.timedelta(days=7)
                    args = (user, time)
                    cur = db.cursor(buffered=True, dictionary=True)
                    cur.execute(query, args)
                    res = cur.fetchall()
                    for x in res:
                        time = x['return_date']
                        if time is None or time == '':
                            timediff = ctime - x['start_d'] - datetime.timedelta(days=7)
                            x['return_date'] = timediff
                    ans = ans + res
                    cur.close()

                return render_template('overdue_return_results.html', borrowings=ans)
        
        if request.form['days'] != '':
            if request.form['days'] < '0':
                flash("Days must be positive integer")
                return redirect(url_for('search'))
            
            if not checkInt(request.form['days']):
                    flash("Days must be integers!")
                    return redirect(url_for('overdue_returns'))

            query = "SELECT * FROM now_borrowed WHERE start_d < %s AND is_returned = 'F';"
            try :
                time = ctime - datetime.timedelta(days=7 + int(request.form['days']))
            except Exception as e:
                    flash(e)
                    return redirect(url_for('overdue_returns')) 
            cur = db.cursor(buffered=True, dictionary=True)
            args = (time,)
            cur.execute(query, args)
            res = cur.fetchall()
            cur.close()
            for x in res:
                time = x['return_date']
                if time is None or time == '':
                    timediff = ctime - x['start_d'] - datetime.timedelta(days=7)
                    x['return_date'] = timediff


            return render_template('overdue_return_results.html', borrowings=res)
    
    return render_template('overdue_returns.html')

@app.route("/review_average", methods=('POST', 'GET'))
@handler_required
def review_average():
    if request.method == 'POST':

        if request.form['user'] != '':
            query = "SELECT * FROM user WHERE username = %s;"
            args = (request.form['user'],)
            cur = db.cursor(buffered=True, dictionary=True)
            cur.execute(query, args)
            ans1 = cur.fetchall()
            cur.close()
            
            if len(ans1) == 0:
                flash("No such user exists.")
                return redirect(url_for('review_average'))

            if request.form['theme'] != '':

                query = "SELECT * FROM theme WHERE theme_name = %s"
                args = (request.form['theme'],)
                cur = db.cursor(buffered=True, dictionary=True)
                cur.execute(query, args)
                themes = cur.fetchall()
                cur.close()
                if len(themes) == 0:
                    flash("No such theme exists.")
                    return redirect(url_for('review_average'))
                
                check = 0
                siz = 0
                for x in themes:
                    query = "SELECT * FROM review WHERE username = %s AND ISBN = %s;"
                    args = (request.form['user'], x['ISBN'])
                    cur = db.cursor(buffered=True, dictionary=True)
                    cur.execute(query, args)
                    reviews = cur.fetchall()
                    siz = siz + len(reviews)
                    for rev in reviews :
                        check = check + rev['scale']
                    cur.close()

                if check == 0:
                    flash("This user has not added a review for this theme..")
                    return redirect(url_for('review_average'))
                result = check / siz
                return render_template('handler_results.html', result=result)
            else :
                query = "SELECT * FROM review WHERE username = %s;"
                args = (request.form['user'],)
                cur = db.cursor(buffered=True, dictionary=True)
                cur.execute(query, args)
                ans = cur.fetchall()
                cur.close()
                counter = len(ans)
                check = 0
                if counter == 0:
                    flash("No reviews by the parameters you specified exist.")
                    return redirect(url_for('review_average'))
                for x in ans:
                    check = check + x['scale']

                result = check / counter
                return render_template("handler_results.html", result=result)
        else :
            if request.form['theme'] != '':
                query = "SELECT * FROM theme WHERE theme_name = %s;"
                args = (request.form['theme'],)
                cur = db.cursor(buffered=True, dictionary=True)
                cur.execute(query, args)
                ans = cur.fetchall()
                cur.close()
                if len(ans) == 0:
                    flash("No such themes exist.")
                    return redirect(url_for('review_average'))
                
                counter = len(ans)
                check = 0
                for x in ans:
                    query = "SELECT * FROM review WHERE ISBN = %s;"
                    args = (x['ISBN'],)
                    cur = db.cursor(buffered=True, dictionary=True)
                    cur.execute(query, args)
                    reviews = cur.fetchall()
                    cur.close()
                    for rev in reviews:
                        check = check + rev['scale']

                result = check / counter
                return render_template("handler_results.html", result=result)
            else :
                flash("Please specify at least one parameter.")
                return redirect(url_for('review_average'))

    
    return render_template('review_average.html')


@app.route("/admin_query1", methods=('GET', 'POST'))
@admin_required
def admin_query1():
    if request.method == 'POST':

        year = request.form['year']
        month = request.form['month']

        if request.form['school_id'] == 'all':
        
            query = """SELECT *
                        FROM now_borrowed
                        WHERE
                        MONTH(start_d) = %s
                        AND YEAR(start_d) = %s
                        ORDER BY school_id ASC;"""
        
            args = (month, year)

        else :

            query = """SELECT *
                        FROM now_borrowed
                        WHERE
                        MONTH(start_d) = %s
                        AND YEAR(start_d) = %s
                        AND school_id = %s;"""
            
            args = (month, year, request.form['school_id'])

        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        borrowings = cur.fetchall()
        cur.close()

        return render_template("query1_res.html", borrowings=borrowings)
    
    # find all the school_names and id's
    query = """SELECT school_id, school_name FROM school;"""
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    res = cur.fetchall()
    cur.close()
    schools = (row for row in res)

    # find all the years in the database
    query = """SELECT DISTINCT 
                EXTRACT(
                YEAR FROM start_d)
                AS year 
                FROM now_borrowed;"""
    
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    res = cur.fetchall()
    cur.close()
    years = (row['year'] for row in res)
    
    return render_template("query1.html", years=years, schools=schools)

@app.route("/admin_query2", methods=('GET', 'POST'))
@admin_required
def admin_query2():

    if request.method == 'POST':

        theme = request.form['theme']

        # first find the authors

        query = """SELECT t.author
                    AS author
                    FROM book t
                    JOIN theme
                    ON
                    t.ISBN = theme.ISBN
                    WHERE theme.theme_name = %s
                    GROUP BY author;"""
        
        args = (theme,)

        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        authors = cur.fetchall()
        cur.close()

        # now find the teachers who borrowed book of this theme in the last year

        query = """SELECT DISTINCT
                    p.first_name AS name,
                    p.last_name AS lastname,
                    p.sex AS sex,
                    p.age as age
                    FROM theme th
                    JOIN
                    book b
                    ON
                    th.ISBN = b.ISBN
                    JOIN
                    now_borrowed borr
                    ON
                    b.ISBN = borr.ISBN
                    JOIN
                    user u
                    ON
                    borr.username = u.username
                    JOIN
                    person p
                    ON
                    u.person_id = p.person_id
                    WHERE
                    th.theme_name = %s
                    AND
                    u.is_student = 'F'
                    AND
                    borr.start_d > %s;"""
        
        ctime = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(days=365)
        args = (theme, ctime)

        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        people = cur.fetchall()
        cur.close()

        return render_template("query2_res.html", authors=authors, theme=theme, people=people)
    
    # find all the themes in the database
    query = """SELECT DISTINCT
                theme_name
                AS th
                FROM theme;"""
    

    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    themes = cur.fetchall()
    cur.close()

    return render_template('query2.html', themes = themes)

@app.route("/admin_query3", methods=('GET', 'POST'))
@admin_required
def admin_query3():

    query = """SELECT
                p.first_name AS name,
                p.last_name AS lastname,
                p.sex,
                p.age,
                COUNT(*)
                AS
                number
                FROM 
                person p
                JOIN
                user u
                ON
                p.person_id = u.person_id
                JOIN
                now_borrowed borr
                ON
                u.username = borr.username
                WHERE 
                u.is_student = 'F'
                AND
                p.age < 40
                GROUP BY
                p.person_id
                ORDER BY
                number
                DESC;"""
    
    cur = db.cursor(buffered=True, dictionary=True)

    cur.execute(query)

    info = cur.fetchall()
    cur.close()
    maxb = info[0]['number']

    return render_template("query3.html", info=info, num=maxb)

@app.route("/admin_query4")
@admin_required
def admin_query4():

    # first query
    # this query returns all the distinct name of the authors that have at least one
    # of their books in the now_borrowed table
    # SELECT DISTINCT b.author FROM book b INNER JOIN now_borrowed ON b.ISBN = now_borrowed.ISBN
    # so now we need to find the authors that are not in this set
    # use left join to exclude the second set
    query = """SELECT DISTINCT b.author
                FROM book b
                LEFT JOIN (
                SELECT DISTINCT author
                FROM book 
                INNER JOIN now_borrowed
                ON book.ISBN = now_borrowed.ISBN
                ) bb 
                ON b.author = bb.author
                WHERE bb.author is NULL
                ORDER BY b.author ASC;"""
    
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    authors = cur.fetchall()
    cur.close()

    return render_template("query4.html", authors=authors)

@app.route("/admin_query5")
@admin_required
def admin_query5():

    # query to find how many borrowings each handler has approved
    # SELECT s.handler_username, COUNT(borr.transaction_id) AS number FROM school s JOIN now_borrowed borr on s.school_id = borr.school_id 
    # GROUP BY s.school_id ORDER BY number DESC;

    ctime = datetime.datetime.now() - datetime.timedelta(days=365)


    
    query1 = """SELECT
                s.school_id, 
                s.handler_name,
                s.handler_surname,
                COUNT(
                DISTINCT
                borr.transaction_id
                )
                AS
                number
                FROM
                school s
                JOIN
                now_borrowed borr
                ON
                s.school_id = borr.school_id
                WHERE
                borr.start_d > %s
                GROUP BY
                s.school_id
                ORDER BY
                number
                DESC
                """
   
    
    query = """SELECT
                t1.handler_name
                AS t1n,
                t1.handler_surname
                AS t1l,
                t2.handler_name
                AS t2n,
                t2.handler_surname
                AS t2l,
                t1.number 
                AS number
                FROM (
                SELECT
                s.school_id, 
                s.handler_name,
                s.handler_surname,
                COUNT(
                DISTINCT
                borr.transaction_id
                )
                AS
                number
                FROM
                school s
                JOIN
                now_borrowed borr
                ON
                s.school_id = borr.school_id
                WHERE
                borr.start_d > %s
                GROUP BY
                s.school_id
                ORDER BY
                number
                DESC
                ) t1,
                (
                SELECT
                s.school_id, 
                s.handler_name,
                s.handler_surname,
                COUNT(
                DISTINCT
                borr.transaction_id
                )
                AS
                number
                FROM
                school s
                JOIN
                now_borrowed borr
                ON
                s.school_id = borr.school_id
                WHERE
                borr.start_d > %s
                GROUP BY
                s.school_id
                ORDER BY
                number
                DESC
                ) t2
                WHERE
                t1.handler_name < t2.handler_name
                AND
                t1.number = t2.number
                AND
                t1.number > 20;"""
    
    args = (ctime, ctime)

    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query, args)

    res = cur.fetchall()
    cur.close()

    if len(res) == 0:
        flash("Either no handler has lended more than 20 books, or no two handlers have lended the same amount of books.")

    return render_template("query5.html", res=res)

@app.route("/admin_query6")
@admin_required
def admin_query6():

    query = """SELECT
                t1.theme_name AS t1,
                t2.theme_name AS t2,
                COUNT(
                borr.transaction_id
                )
                AS
                number
                FROM
                theme t1
                JOIN
                theme t2
                ON
                t1.ISBN = t2.ISBN
                AND
                t1.theme_name < t2.theme_name
                JOIN
                book b
                ON 
                t1.ISBN = b.ISBN
                JOIN
                now_borrowed borr
                ON
                b.ISBN = borr.ISBN
                GROUP BY
                t1.theme_name,
                t2.theme_name
                ORDER BY
                number
                DESC
                LIMIT 3;"""
    
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    res = cur.fetchall()
    cur.close()

    return render_template("query6.html", pairs=res)

@app.route("/admin_query7", methods=('GET', 'POST'))
@admin_required
def admin_query7():

    if request.method == 'POST':
        flash("Not ready yet")
        return redirect(url_for('main_page'))
    
    # this query returns the maximum amount of books
    # a single author has written
    #
    # SELECT COUNT(*) AS max_books FROM book GROUP BY author ORDER BY max_books DESC LIMIT 1;
    #
    # so we need to find the authors that have written 5 less book that this number

    query = """SELECT author,
                COUNT(*)
                AS max_books
                FROM book
                GROUP BY author
                ORDER BY max_books
                DESC LIMIT 1;"""
    
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    ans = cur.fetchone()
    cur.close()

    query = """SELECT author,
                COUNT(*) AS books
                FROM book 
                GROUP BY author 
                HAVING 
                books < (
                SELECT COUNT(*)
                AS max_books
                FROM book
                GROUP BY author
                ORDER BY max_books
                DESC
                LIMIT 1
                ) - 5;"""
    
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    res = cur.fetchall()
    cur.close()

    if len(res) == 0:
        flash("No author fits this category.")
        return redirect(url_for('main_page'))
    
    return render_template("query7.html", authors=res, ans=ans)

# create backup for database
@app.route("/backup")
@admin_required
def backup():
    exit_code = os.system("mysqldump -u root -padmin mydb > src/sql/backup/backup.sql")
    if exit_code == 0:
        flash("Backup successful, saved in src/sql/backup directory.")
    else :
        flash("Backup failed.")
    return redirect(url_for('main_page'))

# restore database from backup
@app.route("/restore")
@admin_required
def restore():
    code1 = os.system("mysql -u root -padmin drop database mydb;")
    if code1 == 256:
        flash("Successfully dropped database.")
    else :
        flash("Failed to drop database.")
        return redirect(url_for('main_page'))
    code2 = os.system("mysql -u root -padmin source src/sql/schema.sql;")
    if code2 == 256:
        flash("Successfully created database.")
    else :
        flash("Failed to create database.")
        return redirect(url_for('main_page'))
    exit_code = os.system("mysql -u root -padmin mydb < src/sql/backup/backup.sql")
    if exit_code == 0:
        flash("Restore successful.")
    else :
        flash("Restore failed.")
    return redirect(url_for('main_page'))

# view school information
@app.route("/school_info", methods=('GET', 'POST'))
@admin_required
def school_info():
    if request.method == 'GET':
        query = "SELECT * FROM school;"
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query)
        schools = cur.fetchall()
        cur.close()
        return render_template("school_info.html", schools=schools)
    
    return redirect(url_for('main_page'))

# edit school information
@app.route("/<int:school_id>/edit_school_info", methods=('GET', 'POST'))
@admin_required
def edit_school_info(school_id):
    if request.method == 'GET':
        query = "SELECT * FROM school WHERE school_id = %s;"
        args = (school_id,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        school = cur.fetchone()
        cur.close()
        return render_template("edit_school_info.html", school=school)
    else :


        query = "SELECT * FROM school WHERE school_id = %s;"
        args = (school_id,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        school = cur.fetchone()
        cur.close()
        school_name = request.form['school_name']
        address = request.form['address']
        city = request.form['city']
        phone = request.form['phone']
        email = request.form['email']
        dname = request.form['dname']
        dsurname = request.form['dsurname']
        hname = request.form['hname']
        hsurname = request.form['hsurname']
        hactivated = request.form['hactivated']
        if phone != '' and not checkInt(phone):
            flash("Phone number must be integers.")
            return redirect(url_for('edit_school_info', school_id=school_id))
        if school_name == '':
            school_name = school['school_name']
        if address == '':
            address = school['address_name']
        if city == '':
            city = school['city']
        if phone == '':
            phone = school['phone_number']
        if email == '':
            email = school['email']
        if dname == '':
            dname = school['director_name']
        if dsurname == '':
            dsurname = school['director_surname']
        if hname == '':
            hname = school['handler_name']
        if hsurname == '':
            hsurname = school['handler_surname']
        if hactivated == '':
            hactivated = school['handler_activated']
        if hactivated != 'T' and hactivated != 'F':
            flash("Handler activated must be T or F.")
            return redirect(url_for('edit_school_info', school_id=school_id))
        if len(city) > 49 or len(address) > 99 or len(school_name) > 99 or len(email) > 49 or len(dname) > 49 or len(dsurname) > 49 or len(hname) > 49 or len(hsurname) > 49:
            flash("Input too long.")
            return redirect(url_for('edit_school_info', school_id=school_id))
        query = """UPDATE school
                    SET
                    school_name = %s,
                    address_name = %s,
                    city = %s,
                    phone_number = %s,
                    email = %s,
                    director_name = %s,
                    director_surname = %s,
                    handler_name = %s,
                    handler_surname = %s,
                    handler_activated = %s
                    WHERE
                    school_id = %s;"""
        args = (school_name, address, city, phone, email, dname, dsurname, hname, hsurname, hactivated, school_id)
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()
        flash("School information updated successfully.")
        return redirect(url_for('edit_school_info', school_id=school_id))