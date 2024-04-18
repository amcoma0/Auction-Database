-- Replace this by the SQL code needed to create your database

CREATE TABLE USERS1
    (USERNAME VARCHAR(10) CONSTRAINT PK_DEPT PRIMARY KEY,
	NAME VARCHAR(50) ,
	CITY VARCHAR(20));
INSERT INTO USERS1 VALUES ('ssmith','Scott Smith','New York');
INSERT INTO USERS1 VALUES ('aking','Allen King','Dallas');
INSERT INTO USERS1 VALUES ('jford','Jones Ford','Chicago');
INSERT INTO USERS1 VALUES ('mmiller','Martin Miller','Boston');

COMMIT;

--UPDATED DATABASE BELOW.

CREATE TABLE users (
	personid SERIAL,
	name	 VARCHAR(512) NOT NULL,
	username VARCHAR(512),
	password VARCHAR(512),
	email	 VARCHAR(512),
	PRIMARY KEY(personid)
);

CREATE TABLE buyer (
	users_personid INTEGER,
	PRIMARY KEY(users_personid)
);

CREATE TABLE seller (
	users_personid INTEGER,
	PRIMARY KEY(users_personid)
);

CREATE TABLE item (
	itemid		 BIGINT,
	seller_users_personid INTEGER NOT NULL,
	buyer_users_personid	 INTEGER NOT NULL,
	PRIMARY KEY(itemid)
);

CREATE TABLE auction (
	auctionid		 SERIAL,
	minprice		 DOUBLE PRECISION,
	auctionenddate	 DATE,
	auctionwinnerid	 INTEGER,
	item_itemid		 BIGINT NOT NULL,
	seller_users_personid INTEGER NOT NULL,
	PRIMARY KEY(auctionid)
);

CREATE TABLE bids (
	amount		 FLOAT(8),
	auction_auctionid	 INTEGER,
	buyer_users_personid INTEGER,
	PRIMARY KEY(amount,auction_auctionid,buyer_users_personid)
);

CREATE TABLE board (
	message		 VARCHAR(512),
	posttime		 TIMESTAMP NOT NULL,
	auction_auctionid INTEGER,
	users_personid	 INTEGER,
	PRIMARY KEY(message,posttime,auction_auctionid,users_personid)
);

CREATE TABLE inbox (
	message	 VARCHAR(512),
	messagetime	 TIMESTAMP,
	subject	 VARCHAR(512),
	users_personid INTEGER,
	PRIMARY KEY(message,messagetime,users_personid)
);

ALTER TABLE buyer ADD CONSTRAINT buyer_fk1 FOREIGN KEY (users_personid) REFERENCES users(personid);
ALTER TABLE seller ADD CONSTRAINT seller_fk1 FOREIGN KEY (users_personid) REFERENCES users(personid);
ALTER TABLE item ADD CONSTRAINT item_fk1 FOREIGN KEY (seller_users_personid) REFERENCES seller(users_personid);
ALTER TABLE item ADD CONSTRAINT item_fk2 FOREIGN KEY (buyer_users_personid) REFERENCES buyer(users_personid);
ALTER TABLE auction ADD CONSTRAINT auction_fk1 FOREIGN KEY (item_itemid) REFERENCES item(itemid);
ALTER TABLE auction ADD CONSTRAINT auction_fk2 FOREIGN KEY (seller_users_personid) REFERENCES seller(users_personid);
ALTER TABLE bids ADD CONSTRAINT bids_fk1 FOREIGN KEY (auction_auctionid) REFERENCES auction(auctionid);
ALTER TABLE bids ADD CONSTRAINT bids_fk2 FOREIGN KEY (buyer_users_personid) REFERENCES buyer(users_personid);
ALTER TABLE board ADD CONSTRAINT board_fk1 FOREIGN KEY (auction_auctionid) REFERENCES auction(auctionid);
ALTER TABLE board ADD CONSTRAINT board_fk2 FOREIGN KEY (users_personid) REFERENCES users(personid);
ALTER TABLE inbox ADD CONSTRAINT inbox_fk1 FOREIGN KEY (users_personid) REFERENCES users(personid);