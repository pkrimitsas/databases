import mysql.connector
db = mysql.connector.connect(host = "localhost", user = "root", password = "admin", database = "mydb")
from faker import Faker
import random
import datetime

fake = Faker('el_GR')
Faker.seed(0)

# create 10 schools
sids = {}
for i in range(1, 11):
    query = """INSERT INTO school(school_id, school_name, address_name, city, phone_number, email, director_name, director_surname, handler_name,\
            handler_surname, handler_username, handler_password, handler_activated) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
    school_id = i
    school_name = fake.company()
    sids[i] = school_name
    address_name = fake.address()
    city = fake.city()
    phone_number = random.randrange(2100000000, 2109999999)
    email = fake.email()
    director_name = fake.first_name()
    director_surname = fake.last_name()
    handler_name = fake.first_name()
    handler_surname = fake.last_name()
    handler_username = fake.unique.user_name()
    handler_password = fake.user_name()
    handler_activated = 'T'

    cur = db.cursor()
    args = (school_id, school_name, address_name, city, phone_number, email, director_name, director_surname, handler_name, handler_surname, handler_username, handler_password, handler_activated)
    cur.execute(query, args)

# create 60 people
for i in range (1, 51):
    query = "INSERT INTO person(person_id, school_id, first_name, last_name, sex, person_type) VALUES (%s, %s, %s, %s, %s, %s);"
    person_id = i
    school_id = random.randrange(1, 11)
    first_name = fake.first_name()
    last_name = fake.last_name()
    choice = random.randrange(1, 3)
    if choice == 1:
        sex = "male"
    elif choice == 2:
        sex = "female"
    choice2 = random.randrange(1, 5)
    if choice2 == 1:
        person_type = "teacher"
    else:
        person_type = "student"

    args = (person_id, school_id, first_name, last_name, sex, person_type)
    cur.execute(query, args)


dict = {}
# create 100 books
for i in range(101):
    query = """INSERT INTO book(school_id, title, publisher, ISBN, author, pages, summary, copies, picture, blanguage, keywords, school_name) \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
    school_id = random.randrange(1, 11)
    title = fake.name()
    school_name = sids[school_id]
    publisher = fake.company()
    ISBN = fake.unique.numerify("###-#-##-######-#")
    dict[i] = ISBN
    author = fake.name()
    pages = random.randrange(100, 1000)
    summary = fake.text()
    copies = random.randrange(1, 10)
    picture = fake.image_url()
    language = fake.country()
    keywords = fake.sentence()

    args = (school_id, title, publisher, ISBN, author, pages, summary, copies, picture, language, keywords, school_name)
    cur.execute(query, args)

# create 10 themes and make sure each book belongs in at least 2
j = 1
index = 1
for i in range (11):
    j = j % 100
    if j == 0:
        j = 1
    query = "INSERT INTO theme(indexer, ISBN, theme_name) VALUES (%s, %s, %s);"
    theme_name = fake.word()
    # insert 11 books into each theme
    for _ in range (12):
        j = j % 100
        if j == 0:
            j = 1
        ISBN = dict[j]
        j = j + 1
        args = (index, ISBN, theme_name)
        index = index + 1
        cur.execute(query, args)

users = {}
# create 50 users
for i in range (1, 51):
    query = "INSERT INTO user(person_id, username, pass, is_active, is_student, school_id) VALUES (%s, %s, %s, %s, %s, %s);"
    person_id = i
    username = fake.unique.user_name()
    password = fake.user_name()
    is_active = 'T'
    # find school id
    nquery = "SELECT school_id, person_type FROM person WHERE person_id = %s;"
    args = (i,)
    curr = db.cursor(buffered=True, dictionary=True)
    curr.execute(nquery, args)
    res = curr.fetchone()
    curr.close()
    school_id = res['school_id']
    if res['person_type'] == 'teacher':
        is_student = 'F'
    elif res['person_type'] == 'student':
        is_student = 'T'
    args = (person_id, username, password, is_active, is_student, school_id)
    users[i] = username
    cur.execute(query, args) 

# create 25 cancelled reservations
i = 1
myarr = random.sample(range(1, 51), 26)
myarr2 = random.sample(range(1, 51), 26)
for k in range (1, 26):
    query = "INSERT INTO reservations(reservation_id, ISBN, tdate, username, rdate, is_active, is_over) VALUES (%s, %s, %s, %s, %s, %s, %s);"
    reservation_id = i
    ISBN = dict[myarr2[k]]
    choice = random.randrange(0, 7)
    tdate = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(days=choice)
    rdate = tdate + datetime.timedelta(days=7)
    is_active = 'F'
    is_over = 'T'
    i = i + 1
    username = users[myarr[k]]
    args = (reservation_id, ISBN, tdate, username, rdate, is_active, is_over)
    cur.execute(query, args)

myarr = random.sample(range(1, 51), 26)
myarr2 = random.sample(range(1, 51), 50)
# create 25 active reservations
p = 0
for k in range (1, 26):
    query = "INSERT INTO reservations(reservation_id, ISBN, tdate, username, rdate, is_active, is_over) VALUES (%s, %s, %s, %s, %s, %s, %s);"
    reservation_id = i
    ISBN = dict[myarr2[p]]
    p = p + 1
    choice = random.randrange(0, 7)
    tdate = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(days=choice)
    rdate = tdate + datetime.timedelta(days=7)
    is_active = 'T'
    is_over = 'F'
    i = i + 1
    username = users[myarr[k]]
    args = (reservation_id, ISBN, tdate, username, rdate, is_active, is_over)
    cur.execute(query, args)


# create 30 borrowings that are completed
myarr = random.sample(range(1, 51), 31)
i = 1
for k in range (1, 26):
    query = "INSERT INTO now_borrowed(transaction_id, ISBN, username, start_d, is_returned, return_date, school_id) VALUES (%s, %s, %s, %s, %s, %s, %s);"
    transaction_id = i
    ISBN = dict[myarr2[k]]
    username = users[myarr[k]]
    choice = random.randrange(1, 25)
    start_d = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(days=choice)
    choice = random.randrange(1, 11)
    is_returned = 'T'
    return_date = start_d + datetime.timedelta(days=random.randrange(1, 6))

    nquery = "SELECT school_id FROM book WHERE ISBN = %s;"
    args = (ISBN,)
    curr = db.cursor(buffered=True, dictionary=True)
    curr.execute(nquery, args)
    res = curr.fetchone()
    curr.close()
    school_id = res['school_id']
    args = (transaction_id, ISBN, username, start_d, is_returned, return_date, school_id)
    i = i + 1
    cur.execute(query, args)

# create 30 borrowings that are not completed
myarr = random.sample(range(1, 51), 31)
for k in range (1, 26):
    query = "INSERT INTO now_borrowed(transaction_id, ISBN, username, start_d, is_returned, return_date, school_id) VALUES (%s, %s, %s, %s, %s, %s, %s);"
    transaction_id = i
    ISBN = dict[myarr2[p]]
    p = p + 1
    username = users[myarr[k]]
    choice = random.randrange(1, 25)
    start_d = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(days=choice)
    choice = random.randrange(1, 11)
    is_returned = 'F'

    nquery = "SELECT school_id FROM book WHERE ISBN = %s;"
    args = (ISBN,)
    curr = db.cursor(buffered=True, dictionary=True)
    curr.execute(nquery, args)
    res = curr.fetchone()
    curr.close()
    school_id = res['school_id']
    args = (transaction_id, ISBN, username, start_d, is_returned, None, school_id)
    i = i + 1
    cur.execute(query, args)

query = "SELECT ISBN, copies FROM book;"
curr = db.cursor(buffered=True, dictionary=True)
curr.execute(query);
res = curr.fetchall()
curr.close()
curr = db.cursor()
for book in res:
    query = 'INSERT INTO currently_available(ISBN, current) VALUES (%s, %s);'
    args = (book['ISBN'], book['copies'])
    curr.execute(query, args)

curr.close()

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
    curr.close()
    

db.commit()
cur.close()
db.close()