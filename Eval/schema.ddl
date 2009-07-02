-- schema.ddl

create table word (
    -- This is where the action is!  See Word page in google code project wiki.

    id integer not null primary key,
    name varchar(255) not null,
    kind int not null references word(id),
    defining_word int not null default 0,
    unique (name)
);


create table answer (
    -- Answers go here.

    id integer not null primary key,
    question_id int not null references answer(id),
    parent int references answer(id),
    position int not null default 1,
    word_id int not null references word(id),

    answer varchar(2000) not null
);

