from flask import render_template, flash, request, url_for, redirect, session
import mysql.connector
from src import app, db
import functools
import datetime

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
    query = "SELECT * FROM currently_available;"
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    current = cur.fetchall()
    cur.close()
    for book in books:
        query = "SELECT school_name FROM school WHERE school_id = %s;"
        arg = (book['school_id'],)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, arg)
        res = cur.fetchone()
        cur.close()
        book['school_id'] = res['school_name']
    return render_template('books.html', books=books, reviews=reviews, current=current)

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

@app.route("/<int:person_id>/my_profile", methods=('POST', 'GET'))
@login_required
def my_profile(person_id):
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
        return render_template('my_profile.html', person=person, user=user)
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
        query = "SELECT username FROM user WHERE person_id = %s;"
        args = (person_id,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        user = cur.fetchone()
        cur.close()
        if first_name == '':
            first_name = person['first_name']
        if last_name == '':
            last_name = person['last_name']
        if sex == '':
            sex = person['sex']
        if username == '':
            username = user['username']
        query = "UPDATE person SET first_name = %s, last_name = %s, sex = %s WHERE person_id = %s;"
        args = (first_name, last_name, sex, person_id)
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()
        query = "UPDATE user SET username = %s WHERE person_id = %s;"
        args = (username, person_id)
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
        flash("Changes were made successfully.")
        return render_template('my_profile.html', person=person, user=user)
    
@app.route("/<string:ISBN>/edit_book", methods=('GET', 'POST'))
@handler_required
def edit_book(ISBN):
    if request.method == 'GET':
        query = "SELECT * FROM book WHERE ISBN = %s;"
        args = (ISBN,)
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        book = cur.fetchone()
        cur.close()
        return render_template('edit_book.html', book=book)
    else:
        try:
            title = request.form['title']
            publisher = request.form['publisher']
            isbn = request.form['ISBN']
            author = request.form['author']
            pages = request.form['pages']
            summary = request.form['summary']
            copies = request.form['copies']
            picture = request.form['picture']
            theme = request.form['theme']
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
            if isbn == '':
                isbn = book['ISBN']
            if author == '':
                author = book['author']
            if pages == '':
                pages = book['pages']
            if summary == '':
                summary = book['summary']
            if copies == '':
                copies == book['copies']
            if picture == '':
                picture = book['picture']
            if theme == '':
                theme == book['theme']
            if language == '':
                language = book['blanguage']
            if keywords == '':
                keywords = book['keywords']
            query = 'UPDATE book SET title = %s, publisher = %s, ISBN = %s, author = %s, pages = %s, summary = %s, copies = %s, picture = %s, theme = %s, blanguage = %s, keywords = %s WHERE ISBN = %s;'
            args = (title, publisher, isbn, author, pages, summary, copies, picture, theme, language, keywords, ISBN)
            cur = db.cursor()
            cur.execute(query, args)
            db.commit()
            cur.close()
            flash("Book was updated successfully.")
            return redirect(url_for('edit_book', ISBN=ISBN))
        except Exception as e:
            flash(e)
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
    if request.method == 'POST':
        school_id = request.form['school_id']
        title = request.form['title']
        publisher = request.form['publisher']
        isbn = request.form['ISBN']
        author = request.form['author']
        pages = request.form['pages']
        summary = request.form['summary']
        copies = request.form['copies']
        picture = request.form['picture']
        theme = request.form['theme']
        language = request.form['language']
        keywords = request.form['keywords']
        query = "INSERT INTO book(school_id, title, publisher, ISBN, author, pages, summary, copies, picture, theme, blanguage, keywords) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        args = (school_id, title, publisher, isbn, author, pages, summary, copies, picture, theme, language, keywords)
        cur = db.cursor()
        try:
            cur.execute(query, args)
            db.commit()
            cur.close()
            flash("New book added successfully.")
            return redirect(url_for('add_book'))
        except Exception as e:
            flash(e)
            return render_template('add_book.html')
        
    return render_template('add_book.html')

@app.route("/search", methods=('GET', 'POST'))
@login_required
def search():
    if request.method == 'POST':
        title = request.form['title']
        publisher = request.form['publisher']
        ISBN = request.form['ISBN']
        author = request.form['author']
        query = "SELECT * FROM currently_available;"
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query)
        current = cur.fetchall()
        cur.close()
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
                query = "SELECT ISBN FROM book WHERE title = %s;"
                args = (title,)
                cur = db.cursor(buffered=True, dictionary=True)
                cur.execute(query, args)
                res2 = cur.fetchone()
                cur.close()
                ISBN = res2['ISBN']
                query = "SELECT * FROM review WHERE ISBN = %s;"
                args = (ISBN,)
                cur = db.cursor(buffered=True, dictionary=True)
                cur.execute(query, args)
                reviews = cur.fetchall()
                cur.close()
                flash("Found the book(s) you requested.")
                return render_template('results.html', books=res, reviews=reviews, current=current)
        if publisher != '':
            query = "SELECT * FROM book WHERE publisher = %s;"
            args = (publisher,)
            cur = db.cursor(buffered=True, dictionary=True)
            cur.execute(query, args)
            res = cur.fetchall()
            cur.close()
            if len(res) == 0:
                flash("No book with the publisher you provided exists in our database.")
                return redirect(url_for('search'))
            else:
                query = "SELECT * FROM book WHERE publisher = %s;"
                args = (publisher,)
                cur = db.cursor(buffered=True, dictionary=True)
                cur.execute(query, args)
                res2 = cur.fetchone()
                cur.close()
                ISBN = res2['ISBN']
                query = "SELECT * FROM review WHERE ISBN = %s;"
                args = (ISBN,)
                cur = db.cursor(buffered=True, dictionary=True)
                cur.execute(query, args)
                reviews = cur.fetchall()
                cur.close()
                flash("Found the book(s) you requested.")
                return render_template('results.html', books=res, reviews=reviews, current=current)
        if ISBN != '':
            query = "SELECT * FROM book WHERE ISBN = %s;"
            args = (ISBN,)
            cur = db.cursor(buffered=True, dictionary=True)
            cur.execute(query, args)
            res = cur.fetchall()
            cur.close()
            if len(res) == 0:
                flash("No book with the ISBN you provided exists in our database.")
                return redirect(url_for('search'))
            else:
                query = "SELECT * FROM review WHERE ISBN = %s;"
                args = (ISBN,)
                cur = db.cursor(buffered=True, dictionary=True)
                cur.execute(query, args)
                reviews = cur.fetchall()
                cur.close()
                flash("Found the book(s) you requested.")
                return render_template('results.html', books=res, reviews=reviews, current=current)
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
                res2 = cur.fetchone()
                cur.close()
                ISBN = res2['ISBN']
                query = "SELECT * FROM review WHERE ISBN = %s;"
                args = (ISBN,)
                cur = db.cursor(buffered=True, dictionary=True)
                cur.execute(query, args)
                reviews = cur.fetchall()
                cur.close()
                flash("Found the book(s) you requested.")
                return render_template('results.html', books=res, reviews=reviews, current=current)
    return render_template('search.html')

@app.route("/<string:ISBN>/make_reservation", methods=('GET', 'POST'))
@login_required
def make_reservation(ISBN):
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
            if x['return_date'] < current_time:
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
            flash("Your reservation was made successfully.")
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
    if request.method == 'POST':
        query = "UPDATE reservations SET is_over = 'T' WHERE reservation_id = %s;"
        args = (reservation_id,)
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()
        flash("Reservation was cancelled successfully.")
        return redirect(url_for('view_reservations'))
    return render_template('books.html')

@app.route("/<string:ISBN>/vreservations")
@handler_required
def vreservations(ISBN):
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
        query = "INSERT INTO now_borrowed(transaction_id, ISBN, username, start_d, is_returned, return_date) VALUES (%s, %s, %s, %s, 'F', %s);"
        args = (id, ISBN, username, tdate, rdate)
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
    if request.method == 'POST':
        ISBN =  request.form['ISBN']
        username = request.form['user']

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
        query = "INSERT INTO now_borrowed(transaction_id, ISBN, username, start_d, is_returned, return_date) VALUES (%s, %s, %s, %s, 'F', %s);"
        tdate = datetime.datetime.now().replace(microsecond=0)
        rdate =  tdate + datetime.timedelta(days=7)
        args = (id, ISBN, username, tdate, rdate)
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
    if request.method == 'POST':

        #check for valid input
        username = request.form['user']
        ISBN = request.form['ISBN']
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
    query = "SELECT * FROM now_borrowed;"
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    borrowings = cur.fetchall()
    cur.close()
    query = "SELECT * FROM reservations;"
    cur = db.cursor(buffered=True, dictionary=True)
    cur.execute(query)
    reservations = cur.fetchall()
    cur.close()
    return render_template('view_borrowings.html', borrowings=borrowings, reservations=reservations)

@app.route("/<int:transaction_id>/make_return", methods=('GET', 'POST'))
@handler_required
def make_return(transaction_id):
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
    if request.method == 'POST':
        username = request.form['user']
        args = (username,)
        query = "SELECT * FROM user WHERE username = %s;"
        cur = db.cursor(buffered=True, dictionary=True)
        cur.execute(query, args)
        user_info = cur.fetchone()
        cur.close()
        if user_info is None:
            flash("No such user exists.")
            return redirect(url_for('books'))
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
    return render_template("main_page.html")
