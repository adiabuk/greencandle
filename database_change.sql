-- Version 3.5

create table api_requests
   (
   `id` INT NOT NULL AUTO_INCREMENT,
   date datetime default now(),
   pair varchar(30),
   text varchar(100),
   action varchar(30),
   price varchar(30),
   strategy varchar(30),
   PRIMARY KEY (`id`)
    );



