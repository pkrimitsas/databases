import mysql.connector
db = mysql.connector.connect(host = "localhost", user = "root", password = "admin", database = "mydb")
from faker import Faker
import random
import datetime

fake = Faker('el_GR')
Faker.seed(0)

# create 10 schools
sids = {}
handler_names = {}
handler_surnames = {}
for i in range(1, 11):
    query = """INSERT INTO school(school_id, school_name, address_name, city, phone_number, email, director_name, director_surname, handler_name,\
            handler_surname, handler_activated) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
    school_id = i
    school_name = fake.company()
    sids[i] = school_name
    address_name = fake.address()
    city = fake.city()
    phone_number = random.randrange(2100000000, 2109999999)
    email = fake.email()
    director_name = fake.first_name()
    director_surname = fake.last_name()
    handler_name = fake.unique.first_name()
    handler_surname = fake.unique.last_name()
    handler_names[i] = handler_name
    handler_surnames[i] = handler_surname 
    #handler_username = fake.unique.user_name()
    #handler_password = fake.user_name()
    handler_activated = 'T'

    cur = db.cursor()
    args = (school_id, school_name, address_name, city, phone_number, email, director_name, director_surname, handler_name, handler_surname, handler_activated)
    cur.execute(query, args)

# create 60 people
for i in range (1, 61):
    query = "INSERT INTO person(person_id, school_id, first_name, last_name, sex, person_type, age) VALUES (%s, %s, %s, %s, %s, %s, %s);"
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
        age = random.randrange(25, 65)
    else:
        person_type = "student"
        age = random.randrange(13, 19)

    args = (person_id, school_id, first_name, last_name, sex, person_type, age)
    cur.execute(query, args)

# create 10 more people who are handlers
o = 61
for i in range (1, 11):
    query = "INSERT INTO person(person_id, school_id, first_name, last_name, sex, person_type, age) VALUES (%s, %s, %s, %s, %s, %s, %s);"
    person_id = o
    o = o + 1
    school_id = i
    first_name = handler_names[i]
    last_name = handler_surnames[i]
    choice = random.randrange(1, 3)
    if choice == 1:
        sex = 'male'
    else :
        sex = 'female'
    person_type = 'handler'
    age = random.randrange(30, 60)
    args = (person_id, school_id, first_name, last_name, sex, person_type, age)
    cur.execute(query, args)

# insert those 10 handlers in handler table
o = 61
for i in range (1, 11):
    query = "INSERT INTO handlers(person_id, school_id, handler_name, handler_surname, handler_username, handler_password) VALUES (%s, %s, %s, %s, %s, %s);"
    person_id = o
    o = o + 1
    school_id = i
    handler_name = handler_names[i]
    handler_surname = handler_surnames[i]
    handler_username = fake.user_name()
    handler_password = fake.user_name()
    args = (person_id, school_id, handler_name, handler_surname, handler_username, handler_password)
    cur.execute(query, args)

author_list = ["author1", "author2", "author3", "author4",
               "author5", "author6", "author7", "author8", "author9", "author10", "no-borrowings-author"]

dict = {}
# create 100 books
image_urls = ["https://m.media-amazon.com/images/I/71jLBXtWJWL._AC_UF1000,1000_QL80_.jpg",
              "https://i2-prod.walesonline.co.uk/incoming/article6890072.ece/ALTERNATES/s615b/hp1.jpg",
              "https://i.imgur.com/IibDqjf.jpg",
              "https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1392127698i/260531.jpg",
              "https://m.media-amazon.com/images/I/710+HcoP38L._AC_UF1000,1000_QL80_.jpg",]
for i in range(101):
    query = """INSERT INTO book(school_id, title, publisher, ISBN, author, pages, summary, copies, picture, blanguage, keywords, school_name) \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
    school_id = random.randrange(1, 11)
    title = fake.name()
    school_name = sids[school_id]
    publisher = fake.company()
    ISBN = fake.unique.numerify("###-#-##-######-#")
    choice = random.randrange(0, 10)
    dict[i] = ISBN
    if i < 100:
        author = author_list[choice]
    else :
        author = author_list[10]
    pages = random.randrange(100, 1000)
    summary = fake.text()
    copies = random.randrange(1, 10)
    im_url = random.randrange(0, 5)
    picture = image_urls[im_url]
    #picture = fake.image_url()
    language = fake.country()
    keywords = fake.sentence()

    args = (school_id, title, publisher, ISBN, author, pages, summary, copies, picture, language, keywords, school_name)
    cur.execute(query, args)

# create 10 themes and make sure each book belongs in at least 2

theme_list = ["science-fiction", "poetry", "literature",
              "technology", "action-adventure", "novel",
              "ancient-greece", "history", "music", "art", "mathematics"]

j = 1
check = random.sample(range(0, 11), 11)
for i in range (11):
    j = j % 100
    if j == 0:
        j = 1
    query = "INSERT INTO theme(indexer, ISBN, theme_name) VALUES (0, %s, %s);"
    theme_name = theme_list[check[i]]
    # insert 11 books into each theme
    for _ in range (1, 12):
        j = j % 101
        if j == 0:
            j = 1
        ISBN = dict[j]
        j = j + 1
        args = (ISBN, theme_name)
        cur.execute(query, args)

users = {}
# create 60 users
for i in range (1, 61):
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
myarr = random.sample(range(1, 61), 26)
myarr2 = random.sample(range(1, 101), 26)
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

# remove the last book with the no-book-author so that we have a book that has not been borrowed nor reserved
dict.popitem()
# create these 2 lists to ensure the 25 active reservation are about different books than the one currently borrowed so we dont get negative copies error
risbn = random.sample(range(1, 100), 60)
ruser = random.sample(range(1, 61), 60)
# create 25 active reservations
p = 0
for k in range (1, 26):
    query = "INSERT INTO reservations(reservation_id, ISBN, tdate, username, rdate, is_active, is_over) VALUES (%s, %s, %s, %s, %s, %s, %s);"
    reservation_id = i
    # 25 different ISBN's
    ISBN = dict[risbn[p]]
    p = p + 1
    choice = random.randrange(0, 7)
    tdate = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(days=choice)
    rdate = tdate + datetime.timedelta(days=7)
    is_active = 'T'
    is_over = 'F'
    i = i + 1
    # 25 different users
    username = users[ruser[p]]
    args = (reservation_id, ISBN, tdate, username, rdate, is_active, is_over)
    cur.execute(query, args)


# create 500 borrowings that are completed
i = 1
for _ in range (1, 501):
    query = "INSERT INTO now_borrowed(transaction_id, ISBN, username, start_d, is_returned, return_date, school_id) VALUES (%s, %s, %s, %s, %s, %s, %s);"
    transaction_id = i
    choice = random.randrange(0, 100)
    ISBN = dict[choice]
    choice = random.randrange(1, 60)
    username = users[choice]
    choice = random.randrange(1, 364)
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
for k in range (1, 26):
    query = "INSERT INTO now_borrowed(transaction_id, ISBN, username, start_d, is_returned, return_date, school_id) VALUES (%s, %s, %s, %s, %s, %s, %s);"
    transaction_id = i
    # to ensure different books are now_borrowed
    ISBN = dict[risbn[p]]
    # to ensure different users have borrowed these books
    username = users[ruser[p]]
    p = p + 1
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

# create 50 reviews
for k in range (1, 51):
    query = "INSERT INTO review(review_id, ISBN, username, opinion, is_approved, scale) VALUES (0, %s, %s, %s, %s, %s);"
    choice = random.randrange(1, 100)
    ISBN = dict[choice]
    choice = random.randrange(1, 60)
    username = users[choice]
    opinion = fake.text()
    choice = random.randrange(1, 6)
    if choice > 1:
        is_approved = 'T'
    else :
        is_approved = 'F'
    choice = random.randrange(1, 6)
    args = (ISBN, username, opinion, is_approved, choice)
    cur.execute(query, args)

query = "SELECT ISBN, copies FROM book;"
curr = db.cursor(buffered=True, dictionary=True)
curr.execute(query);
res = curr.fetchall()
curr.close()
for book in res:
    query = 'INSERT INTO currently_available(ISBN, current) VALUES (%s, %s);'
    args = (book['ISBN'], book['copies'])
    cur.execute(query, args)

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