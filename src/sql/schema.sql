
-- create database and tables for project


CREATE SCHEMA mydb;
USE mydb;

-- school(school_id, school_name, address_name, city, phone_number, email, director_name, director_surname, handler_name, handler_surname, handler_activated)
create table school (
        school_id int unsigned not null auto_increment,
        school_name varchar(100) not null,
        address_name varchar(100) not null,
        city varchar(50) not null,
        phone_number int unsigned not null,
        email varchar(50) not null,
        director_name varchar(50) not null,
        director_surname varchar(50) not null,
        handler_name varchar(50) not null,
        handler_surname varchar(50) not null,
        handler_activated char(1),
        primary key (school_id),
        unique (school_name),
        unique (handler_name),
        unique (handler_surname),
    constraint ck_handler_activated check (handler_activated in ('T', 'F'))
);

-- person(person_id, school_id, first_name, last_name, sex, person_type, age)
create table person (
        person_id int unsigned not null auto_increment,
        school_id int unsigned not null,
        first_name varchar(50) not null,
        last_name varchar(50) not null,
        sex varchar(15) not null,
        person_type varchar(50) not null,
        age int unsigned not null,
        primary key (person_id),
    constraint ck_age check (age > 0),
    constraint fk_school_id foreign key (school_id) references school (school_id) on delete cascade on update cascade
);

-- handlers(person_id, school_id, handler_name, handler_surname, handler_username, handler_password)
create table handlers (
        person_id int unsigned not null,
        school_id int unsigned not null,
        handler_name varchar(50) not null,
        handler_surname varchar(50) not null,
        handler_username varchar(50) not null,
        handler_password varchar(50) not null,
        primary key (person_id),
        unique (handler_username),
    constraint fk_hname foreign key (handler_name) references school (handler_name) on delete cascade on update cascade,
    constraint fk_hsurname foreign key (handler_surname) references school (handler_surname) on delete cascade on update cascade,
    constraint fk_handl_school_id foreign key (school_id) references school (school_id) on delete cascade on update cascade,
    constraint fk_handl_person_id foreign key (person_id) references person (person_id) on delete cascade on update cascade
);

-- user(person_id, username, pass, is_active, is_student, school_id)
create table user (
        person_id int unsigned not null,
        username varchar(50) not null,
        pass varchar(50) not null,
        is_active char(1),
        is_student char(1) not null,
        school_id int unsigned not null,
        primary key (person_id),
    constraint ck_username unique(username),
    constraint fk_school_id_user foreign key (school_id) references school (school_id) on delete cascade on update cascade,
    constraint ck_is_active check (is_active in ('T', 'F')),
    constraint ck_is_student check (is_student in ('T', 'F')),
    constraint fk_person_id foreign key (person_id) references person (person_id) on delete cascade on update cascade    
);

-- book(school_id, title, publisher, ISBN, author, pages, summary, copies, picture, blanguage, keywords, school_name)
create table book (
        school_id int unsigned not null,
        title varchar(200) not null,
        publisher varchar(50) not null,
        ISBN varchar(17) not null,
        author varchar(50) not null,
        pages int unsigned not null,
        summary text not null,
        copies int unsigned not null,
        picture text not null,
        blanguage varchar(50) not null,
        keywords text not null,
        school_name varchar(100) not null,
        primary key (ISBN),
    constraint ck_copies check (copies > 0),
    constraint fk_shool_name foreign key (school_name) references school (school_name) on delete cascade on update cascade,
    constraint ck_pages check (pages > 0),
    constraint fk_book_school_id foreign key (school_id) references school (school_id) on delete cascade on update cascade
);

-- review(review_id, ISBN, username, opinion, is_approved)
create table review (
        review_id int unsigned not null auto_increment,
        ISBN varchar(17) not null,
        username varchar(50) not null,
        opinion text not null,
        is_approved char(1),
        scale int unsigned not null,
        primary key (review_id),
    constraint ck_scale check (scale > 0 and scale < 6),
    constraint ck_is_approved check (is_approved in ('T', 'F')),
    constraint fk_review_ISBN foreign key (ISBN) references book (ISBN) on delete cascade on update cascade,
    constraint fk_review_username foreign key (username) references user (username) on delete cascade on update cascade    
);


-- currently_available(ISBN, current)
create table currently_available (
        ISBN varchar(17) not null,
        current int unsigned not null,
        primary key (ISBN),
    constraint ck_curr check (current >= 0),
    constraint fk_curr_ISBN foreign key (ISBN) references book (ISBN) on delete cascade on update cascade
);

-- reservations(reservation_id, ISBN, tdate, username, rdate, is_active, is_over)
create table reservations (
        reservation_id int unsigned not null auto_increment,
        ISBN varchar(17) not null,
        tdate timestamp not null,
        username varchar(50) not null,
        rdate timestamp not null,
        is_active char(1) not null,
        is_over char(1) not null,
        primary key (reservation_id),
    constraint ck_is_active_res check (is_active in ('T', 'F')),
    constraint ck_is_over_res check (is_over in ('T', 'F')),
    constraint fk_reserv_ISBN foreign key (ISBN) references book (ISBN) on delete cascade on update cascade,
    constraint fk_user_reserv foreign key (username) references user (username) on delete cascade on update cascade
);

-- now_borrowed(transaction_id, ISBN, username, start_d, is_returned, return_date, school_id)
create table now_borrowed (
        transaction_id int unsigned not null auto_increment,
        ISBN varchar(17) not null,
        username varchar(50) not null,
        start_d timestamp not null,
        is_returned char(1),
        return_date timestamp,
        school_id int unsigned not null,
        primary key (transaction_id),
    constraint fk_school_id_reserv foreign key (school_id) references school (school_id) on delete cascade on update cascade,
    constraint fk_ISBN_now foreign key (ISBN) references book (ISBN) on delete cascade on update cascade,
    constraint fk_user_now foreign key (username) references user (username) on delete cascade on update cascade,
    constraint ck_bool check (is_returned in ('T', 'F'))
);

-- theme(indexer, ISBN, theme_name)
create table theme (
        indexer int unsigned not null auto_increment,
        ISBN varchar(17) not null,
        theme_name varchar(150) not null,
        primary key (indexer),
    constraint fk_ISBN_theme foreign key (ISBN) references book (ISBN) on delete cascade on update cascade
);