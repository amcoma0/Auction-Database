-- Replace this by the SQL code needed to create your database

CREATE TABLE USERS
    (USERNAME VARCHAR(10) CONSTRAINT PK_DEPT PRIMARY KEY,
	NAME VARCHAR(50) ,
	CITY VARCHAR(20));
INSERT INTO USERS VALUES ('ssmith','Scott Smith','New York');
INSERT INTO USERS VALUES ('aking','Allen King','Dallas');
INSERT INTO USERS VALUES ('jford','Jones Ford','Chicago');
INSERT INTO USERS VALUES ('mmiller','Martin Miller','Boston');

COMMIT;

CREATE TABLE person (
	personid INTEGER,
	name	 VARCHAR(512) NOT NULL,
	PRIMARY KEY(personid)
);

CREATE TABLE buyer (
	person_personid INTEGER,
	PRIMARY KEY(person_personid)
);

CREATE TABLE seller (
	person_personid INTEGER,
	PRIMARY KEY(person_personid)
);

CREATE TABLE auction (
	auctionid					 INTEGER,
	minprice						 DOUBLE PRECISION,
	auctionenddate					 DATE,
	auctionwinnerid					 INTEGER,
	highestbid					 DOUBLE PRECISION,
	itemid						 BIGINT,
	seller_person_personid				 INTEGER,
	weakentitytransaction_item_seller_person_personid INTEGER,
	weakentitytransaction_item_buyer_person_personid	 INTEGER,
	PRIMARY KEY(auctionid,seller_person_personid,weakentitytransaction_item_seller_person_personid,weakentitytransaction_item_buyer_person_personid)
);

CREATE TABLE weakentitytransaction_item (
	sellerid		 INTEGER,
	buyerid		 INTEGER,
	transactionamount	 DOUBLE PRECISION,
	itemid			 BIGINT,
	item_itemid		 BIGINT NOT NULL,
	seller_person_personid	 INTEGER,
	buyer_person_personid	 INTEGER,
	seller_person_personid1 INTEGER NOT NULL,
	buyer_person_personid1	 INTEGER NOT NULL,
	PRIMARY KEY(seller_person_personid,buyer_person_personid)
);

ALTER TABLE buyer ADD CONSTRAINT buyer_fk1 FOREIGN KEY (person_personid) REFERENCES person(personid);
ALTER TABLE seller ADD CONSTRAINT seller_fk1 FOREIGN KEY (person_personid) REFERENCES person(personid);
ALTER TABLE auction ADD CONSTRAINT auction_fk1 FOREIGN KEY (seller_person_personid) REFERENCES seller(person_personid);
ALTER TABLE auction ADD CONSTRAINT auction_fk2 FOREIGN KEY (weakentitytransaction_item_seller_person_personid, weakentitytransaction_item_buyer_person_personid) REFERENCES weakentitytransaction_item(seller_person_personid, buyer_person_personid);
ALTER TABLE weakentitytransaction_item ADD UNIQUE (item_itemid);
ALTER TABLE weakentitytransaction_item ADD CONSTRAINT weakentitytransaction_item_fk1 FOREIGN KEY (seller_person_personid) REFERENCES seller(person_personid);
ALTER TABLE weakentitytransaction_item ADD CONSTRAINT weakentitytransaction_item_fk2 FOREIGN KEY (buyer_person_personid) REFERENCES buyer(person_personid);
ALTER TABLE weakentitytransaction_item ADD CONSTRAINT weakentitytransaction_item_fk3 FOREIGN KEY (seller_person_personid1) REFERENCES seller(person_personid);
ALTER TABLE weakentitytransaction_item ADD CONSTRAINT weakentitytransaction_item_fk4 FOREIGN KEY (buyer_person_personid1) REFERENCES buyer(person_personid);

COMMIT;
