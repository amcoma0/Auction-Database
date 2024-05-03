## ITCS 3160-0002, Spring 2024
## Marco Vieira, marco.vieira@charlotte.edu
## University of North Carolina at Charlotte
import datetime
import random

## Alex Mccomas, Ramone Thompson, Derrick Moore
 
## IMPORTANT: this file includes the Python implementation of the REST API
## It is in this file that you should implement the functionalities/transactions   

import flask
import logging, psycopg2, time, jwt

from functools import wraps

app = flask.Flask(__name__)

StatusCodes = {
    'success': 200,
    'api_error': 400,
    'internal_error': 500
}

##########################################################
## DATABASE ACCESS
##########################################################

def db_connection():
    db = psycopg2.connect(
        user = "scott",
        password = "tiger",
        host = "db",
        port = "5432",
        database = "dbproj"
    )
    
    return db






##########################################################
## ENDPOINTS
##########################################################


## Create a new user. (complete)
##
## To use it, you need to use postman or curl:
##
## curl -X POST http://localhost:8080/users/ -H 'Content-Type: application/json' -d '{"username": "ppopov", "password": "test", "name": "Peter Popov", "email": "random@gmail.com"}'
##

@app.route('/user', methods=['POST'])
def add_user():
    logger.info('POST /users')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'POST /users - payload: {payload}')

    # do not forget to validate every argument, e.g.,:
    if 'username' not in payload or 'email' not in payload or 'password' not in payload or 'name' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'Missing inputs.'}
        return flask.jsonify(response)

    # parameterized queries, good for security and performance
    statement = 'INSERT INTO users (username, name, email, password) VALUES (%s, %s, %s, %s)'
    values = (payload['username'], payload['name'], payload['email'], payload['password'])

    try:
        cur.execute(statement, values)

        # commit the transaction
        conn.commit()
        response = {'status': StatusCodes['success'], 'results': f'Inserted users {payload["username"]}'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /users - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

## The below code is the code for the landing page of our auction site. (complete)
##
## Landing page
##
## To use the below function, make sure the db-proj-api is running in docker and paste the following into
## a web browser:
##
## http://localhost:8080/

@app.route('/')
def landing_page():
    return """

    Welcome to team RDA's auction site!  <br/>
    <br/>
    Team members: Ramone Thompson, Derrick Moore, Alex McComas <br/>
    <br/>
    ITCS 3160-002, Spring 2024<br/>
    <br/>
    """

## User Authentication.
##
## This function allows a user to login with already created credentials
##
## Use postman to test, put data into JSON format in the request

@app.route('/login', methods=['PUT'])
def login_user():
    auth = flask.request.get_json()

    if not auth or 'username' not in auth \
            or 'password' not in auth:
        return flask.make_response('missing credentials', 401)
    try:
        conn = db_connection()
        cur = conn.cursor()
        statement = 'select 1 from users where username = %s and password = %s'
        values = (auth['username'], auth['password'])
        cur.execute(statement, values)
        if cur.rowcount == 0:
            response = ('could not verify', 401)
        else:
            response = auth['username'] + str(random.randrange(111111111, 999999999))
            statement = "insert into tokens values( %s, %s , current_timestamp + (60 * interval '1 min'))"
            values = (auth['username'], response)
            cur.execute(statement, values)
            conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /users - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return response


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None

        if 'access-token' in flask.request.headers:
            token = flask.request.headers['access-token']

        if not token:
            return flask.jsonify({'message': 'invalid token'})

        try:
            conn = db_connection()
            cur = conn.cursor()

            cur.execute("delete from tokens where timeout < current_timestamp")
            conn.commit()
            cur.execute("select username from tokens where token = %s", (token,))

            if cur.rowcount==0:
                return flask.jsonify({'message': 'invalid token'})

            else:
                current_user = cur.fetchone()[0]

        except (Exception) as error:
            logger.error(f'POST /users - error: {error}')
            conn.rollback()
            return flask.jsonify({'message': 'inavlid token'})

        return f(current_user, *args, **kwargs)

    return decorator
## Create a new auction.
##
## This function allows a user to create a new auction
##
## Login to the application first to get a token, then use postman to create the auction from
## http://localhost:8080/dbproj/auction
##
## When creating auction, format date as 'YYYY-MM-DD'

@app.route("/dbproj/auction", methods=['POST'])
@token_required
def create_auction(current_user):
    logger.info('POST /auction')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'POST /auction - payload: {payload}')

    # do not forget to validate every argument, e.g.,:
    if 'minprice' not in payload or 'auctionenddate' not in payload or 'title' not in \
            payload or 'description' not in payload or 'item_itemid' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'Missing inputs.'}
        return flask.jsonify(response)

    cur.execute('SELECT username FROM tokens WHERE current_user = tokens.token')
    username = cur.fetchone()

    cur.execute('SELECT personid FROM users WHERE username = users.username')
    userid = cur.fetchone()

    # parameterized queries, good for security and performance
    statement = 'INSERT INTO auction (auctionstate, minprice, auctionenddate, title, description, item_itemid, seller_users_personid) \
    VALUES (%s, %s, %s, %s, %s, %s, %s)'
    values = ('open', payload['minprice'], payload['auctionenddate'], payload['title'],
              payload['description'], payload['item_itemid'], userid)


    try:
        cur.execute(statement, values)

        # commit the transaction
        conn.commit()
        response = {'status': StatusCodes['success'], 'results': f'Created Auction {payload["title"]}'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /auction - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


## List all existing auctions. (complete)
##
## This function lists all the existing auctions in the auctions table.
##
## use postman.

@app.route("/auctions", methods=['GET'])
@token_required
def get_all_auctions(current_user):
    logger.info("###   DEMO: GET /auctions   ###")

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT auctionid, item_itemid, auctionstate FROM auction")
    rows = cur.fetchall()

    payload = []
    logger.info("---- auctions ----")
    for row in rows:
        logger.info(row)
        content = {'auctionid': int(row[0]), 'item_itemid': row[1], 'auctionstate': row[2]}
        payload.append(content)# payload to be returned

    conn.close ()

    return flask.jsonify(payload)



## Search existing auctions.
##
## This function searches the available auctions with the keyword that relates to one or multiple auctions
##
## Use postman or cURL

@app.route("/dbproj/searchauctions/", methods=['GET'])
@token_required
def search_auctions(keyword, current_user):
    logger.info('GET /auctions/<keyword>')

    logger.debug('auction: {keyword}')

    conn = db_connection()
    cur = conn.cursor()



    try:
        cur.execute('SELECT auctionid, minprice, item_itemid FROM auction where auctionid = %s', (keyword,))
        rows = cur.fetchall()

        row = rows[0]

        logger.debug('GET /auctions/<keyword> - parse')
        logger.debug(row)
        content = {'Auction ID': row[0], 'Minimum Price': row[1], 'Item ID': row[2]}

        response = {'status': StatusCodes['success'], 'results': content}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /auctions/<keyword> - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


## Retrieve details of an auction
##
## (insert description of function) Retrieves the details of an auction based on the item id number
##
## (insert how to test/run function)
@app.route('/dbproj/auction/<auctionid>', methods=['GET'])
def get_details(auctionid):
    logger.info(f'GET /dbproj/auction/<auctionid>')

    logger.debug('item_itemid: {auctionid}')

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT minprice, auctionenddate, title, description, item_itemid, auctionid FROM auction where auctionid = %s', (auctionid,))
        rows = cur.fetchall()

        row = rows[0]

        logger.debug('GET /dbproj/auction/<item_itemid> - parse')
        logger.debug(row)
        content = {'minprice': row[0], 'auctionenddate': row[1], 'title': row[2], 'description': row[3], 'item_itemid': row[4], 'auctionid': row[5]}

        response = {'status': StatusCodes['success'], 'results': content}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /dbproj/auction/{auctionid} - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


    


## List all auctions in which the user has activity. (complete)
##
## This function lists all the auctions in which the user has activity as a buyer or seller.
##
## Use postman

@app.route("/userAuctions", methods=['GET'])
@token_required
def get_all_userAuctions(current_user):
    logger.info("###   DEMO: GET /userAuctions   ###")

    conn = db_connection()
    cur = conn.cursor()

    cur.execute('SELECT DISTINCT auctionid, description, auctionenddate FROM auction, bids, users WHERE ((auction.seller_users_personid = users.personid) OR (auction.auctionwinnerid = users.personid) OR (auction.auctionid = bids.auction_auctionid AND bids.buyer_users_personid = users.personid)) AND users.username = %s', (current_user,))
    rows = cur.fetchall()

    payload = []
    logger.info("---- user auctions  ----")
    for row in rows:
        logger.info(row)
        content = {'auctionid':int(row[0]), 'description':row[1]}
        payload.append(content) # payload to be returned

    conn.close()

    return flask.jsonify(payload)


## Place a bid in an auction.
##
## (insert description of function)
##
## (insert how to test/run function)

@app.route('/dbproj/bid/', methods=['POST'])
@token_required
def place_bid(current_user):
    logger.info('POST /bid')
    payload = flask.request.get_json()
    token = flask.request.headers['access-token']

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'POST / - payload: {payload}')

    if 'bid' not in payload or 'auctionid' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'Missing inputs.'}
        return flask.jsonify(response)

    try:
        cur.execute("SELECT auctionenddate FROM auction WHERE auctionid = auction.auctionid")
        auctionenddate = cur.fetchone()

        # auctionenddate = auctionenddate[0]
        #
        # if isinstance(auctionenddate, datetime.datetime):
        #     auctionenddate = auctionenddate.date()
        #
        # current_date = datetime.date.today()
        #
        # if current_date > auctionenddate:
        #     response = {'status': StatusCodes['api_error'], 'results': 'Auction has already ended'}
        #     return flask.jsonify(response)

        cur.execute("SELECT minprice FROM auction WHERE auctionid = auction.auctionid")
        minprice = cur.fetchone()

        if payload['bid'] < str(minprice[0]):
            response = {'status': StatusCodes['api_error'], 'results': 'You must bid more than the minimum price'}
            return flask.jsonify(response)

        cur.execute("SELECT auctionstate FROM auction WHERE auctionid = %s", (payload['auctionid'],))
        auctionstate = cur.fetchone()

        if str(auctionstate[0]) == 'closed':
            response = {'status': StatusCodes['api_error'], 'results': 'This auction is canceled, sorry'}
            return flask.jsonify(response)

        cur.execute('SELECT username FROM tokens WHERE tokens.token = %s', (token,))
        username = cur.fetchone()

        cur.execute('SELECT personid FROM users WHERE users.username = %s', (username,))
        userid = cur.fetchone()

        # parameterized queries, good for security and performance
        statement = 'INSERT INTO bids (amount, auction_auctionid, buyer_users_personid) VALUES (%s, %s, %s)'
        values = (payload['bid'], payload['auctionid'], userid)

        cur.execute(statement, values)

        # commit the transaction
        conn.commit()
        response = {'status': StatusCodes['success'], 'results': f'Inserted bid {payload["bid"]}'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /users - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)



## Edit properties of an auction.
##
## (insert description of function)
##
## (insert how to test/run function)

@app.route('/dbproj/auction/<auctionid>', methods=['PUT'])
@token_required
def edit_auction(current_user, auctionid):
    logger.info('PUT /dbproj/auction/<auctionid>')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'PUT /dbproj/auction/<auctionid> - payload: {payload}')

    # do not forget to validate every argument, e.g.,:
    if 'minprice' not in payload or 'auctionenddate' not in payload or 'title' not in payload or 'description' not in payload or 'item_itemid' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'Missing Inputs'}
        return flask.jsonify(response)


    # parameterized queries, good for security and performance
    statement = 'UPDATE auction SET minprice = %s , auctionenddate = %s , title = %s , description = %s , item_itemid = %s WHERE auctionid = %s'
    values = (payload['minprice'], payload['auctionenddate'], payload['title'], payload['description'], payload['item_itemid'], auctionid)

    try:
        res = cur.execute(statement, values)
        response = {'status': StatusCodes['success'], 'results': f'Updated: {cur.rowcount}'}

        # commit the transaction
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


## Write a message on the auction's board. (complete) 
##
## This function adds a message to the board table.
##
## Use postman.

@app.route('/messageBoard', methods=['POST'])
@token_required
def add_messageBoard(current_user):
    logger.info('POST /messageBoard')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'POST /messageBoard - payload: {payload}')

    # do not forget to validate every argument, e.g.,:
    if 'message' not in payload or 'auction_auctionid' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'Missing inputs.'}
        return flask.jsonify(response)

    posttime = datetime.datetime.now()

    cur.execute('SELECT username FROM tokens WHERE current_user = tokens.token')
    username = cur.fetchone()

    cur.execute('SELECT personid FROM users WHERE username = users.username')
    userid = cur.fetchone()

    # parameterized queries, good for security and performance
    statement = 'INSERT INTO board (message, posttime, auction_auctionid, users_personid) VALUES (%s, %s, %s, %s)'
    values = (payload['message'], posttime, payload['auction_auctionid'], userid)

    try:
        cur.execute(statement, values)

        # commit the transaction
        conn.commit()
        response = {'status': StatusCodes['success'], 'results': f'Inserted message {payload["message"]}'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /messageBoard - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


## Immediate delivery of messages to users.
##
## (insert description of function)
##
## (insert how to test/run function)
@app.route('/inbox', methods=['GET'])
@token_required
def receive_messages(current_user):
    logger.info('GET /inbox')
    token = flask.request.headers['access-token']

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT username FROM tokens WHERE tokens.token = %s', (token,))
        username = cur.fetchone()

        cur.execute('SELECT personid FROM users WHERE users.username = %s', (username,))
        userid = cur.fetchone()

        cur.execute('SELECT message, posttime FROM board WHERE board.users_personid = %s', (userid,))
        rows = cur.fetchall()

        logger.debug('GET /inbox - parse')
        Results = []
        for row in rows:
            logger.debug(row)
            content = {'message': row[0], 'posttime': row[1]}
            Results.append(content)  # appending to the payload to be returned

        response = {'status': StatusCodes['success'], 'results': Results}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /inbox - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


## Outbid notification.
##
## (insert description of function)
##
## (insert how to test/run function)

@app.route('/messageBoard', methods=['POST'])
@token_required
def outbid_notification(current_user):
    logger.info('POST /messageBoard')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'POST /messageBoard - payload: {payload}')

    # do not forget to validate every argument, e.g.,:
    if 'message' not in payload or 'auctionid' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'Missing inputs.'}
        return flask.jsonify(response)

    posttime = datetime.datetime.now()

    cur.execute('SELECT username FROM tokens WHERE current_user = tokens.token')
    username = cur.fetchone()

    cur.execute('SELECT personid FROM users WHERE username = users.username')
    userid = cur.fetchone()

    # Get the minimum price of the auction
    cur.execute('SELECT minprice FROM auction WHERE auctionid = %s', (payload['auctionid'],))
    minprice = cur.fetchone()[0]

    # Check if the bid amount is greater than the minimum price
    if 'bid' in payload and float(payload['bid']) > minprice:
        # parameterized queries, good for security and performance
        statement = 'INSERT INTO board (message, posttime, auctionid, users_personid) VALUES (%s, %s, %s, %s)'
        values = (payload['message'], posttime, payload['auctionid'], userid)

        try:
            cur.execute(statement, values)

            # commit the transaction
            conn.commit()
            response = {'status': StatusCodes['success'], 'results': f'Inserted message {payload["message"]}'}

        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(f'POST /messageBoard - error: {error}')
            response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

            # an error occurred, rollback
            conn.rollback()

    else:
        response = {'status': StatusCodes['api_error'], 'results': 'Bid amount must be greater than the minimum price.'}

    if conn is not None:
        conn.close()

    return flask.jsonify(response)


## Close auction. (complete)
##
## (insert description of function)
##
## Use postman.
@app.route('/close', methods=['PUT'])
def closeAuction():
    logger.info('PUT /close')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    if 'auctionid' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'auctionid is required to close an auction'}
        return flask.jsonify(response)

    cur.execute('SELECT buyer_users_personid FROM bids WHERE auction_auctionid = %s and amount >= ALL (select amount from bids where auction_auctionid = %s)',(payload['auctionid'],payload['auctionid']))
    maxBidUser = cur.fetchone()

    statement = 'UPDATE auction SET auctionstate = %s, auctionwinnerid = %s WHERE auctionid = %s'
    values = ('closed', maxBidUser, payload['auctionid'])

    auctionid = payload['auctionid']

    try:
        res = cur.execute(statement, values)
        response = {'status': StatusCodes['success'], 'results': f'Closed auction with id: {auctionid}'}

        # commit the transaction
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(payload)




## Cancel an auction.
##
## (insert description of function)
##
## (insert how to test/run function)
@app.route("/cancelAuction", methods=["PUT"])
@token_required
def cancelAuction(current_user):
    logger.info('PUT /cancelAuction')
    payload = flask.request.get_json()
    token = flask.request.headers['access-token']  # FIXED

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'PUT /cancelAuction - payload: {payload}')

    # do not forget to validate every argument, e.g.,:
    if 'auctionid' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'auctionid is required to cancel an auction'}
        return flask.jsonify(response)

    try:  # MOVED HERE - all DB statments should be in a try block
        cur.execute('SELECT username FROM tokens WHERE tokens.token = %s', (token,))  # FIXED
        username = cur.fetchone()[0]  # FIXED

        cur.execute('SELECT personid FROM users WHERE users.username = %s', (username,))
        userid = cur.fetchone()

        # parameterized queries, good for security and performance
        cur.execute('SELECT buyer_users_personid FROM bids WHERE auction_auctionid = %s', (payload['auctionid'],))
        all_buyers_userid = cur.fetchall()

        for userid in all_buyers_userid:
            cur.execute(
                'INSERT INTO board (message, posttime, auction_auctionid, users_personid) VALUES (%s, %s, %s, %s)',
                ('This auction has been canceled'), (datetime.datetime.now()), payload['auctionid'], userid)

        statement = 'UPDATE auction SET auctionstate = %s WHERE auctionid = %s AND seller_users_personid = %s'
        values = ('canceled', payload['auctionid'], userid)

        auctionid = payload['auctionid']

        res = cur.execute(statement, values)
        response = {'status': StatusCodes['success'], 'results': f'Canceled auction: {auctionid}'}

        # commit the transaction
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)








## THIS IS AN EXAMPLE BELOW.

##
## Demo GET
##
## Obtain all users in JSON format
##
## To use it, access:
##
## http://localhost:8080/users/
##

@app.route('/users/', methods=['GET'])
def get_all_users():
    logger.info('GET /users')

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT username, name, city FROM users1')
        rows = cur.fetchall()

        logger.debug('GET /users - parse')
        Results = []
        for row in rows:
            logger.debug(row)
            content = {'username': row[0], 'name': row[1], 'city': row[2]}
            Results.append(content)  # appending to the payload to be returned

        response = {'status': StatusCodes['success'], 'results': Results}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /users - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

## THIS IS AN EXAMPLE BELOW.

##
## Demo GET
##
## Obtain user with username <username>
##
## To use it, access:
##
## http://localhost:8080/users/ssmith
##

@app.route('/users/<username>/', methods=['GET'])
def get_user(username):
    logger.info('GET /users/<username>')

    logger.debug('username: {username}')

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT username, name, city FROM users1 where username = %s', (username,))
        rows = cur.fetchall()

        row = rows[0]

        logger.debug('GET /users/<username> - parse')
        logger.debug(row)
        content = {'username': row[0], 'name': row[1], 'city': row[2]}

        response = {'status': StatusCodes['success'], 'results': content}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /users/<username> - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

## THIS IS AN EXAMPLE BELOW.

##
## Demo POST
##
## Add a new user in a JSON payload
##
## To use it, you need to use postman or curl:
##
## curl -X POST http://localhost:8080/users/ -H 'Content-Type: application/json' -d '{"city": "London", "username": "ppopov", "name": "Peter Popov"}'
##

@app.route('/users/', methods=['POST'])
def add_users():
    logger.info('POST /users')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'POST /users - payload: {payload}')

    # do not forget to validate every argument, e.g.,:
    if 'username' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'username value not in payload'}
        return flask.jsonify(response)

    # parameterized queries, good for security and performance
    statement = 'INSERT INTO users1 (username, name, city) VALUES (%s, %s, %s)'
    values = (payload['username'], payload['city'], payload['name'])

    try:
        cur.execute(statement, values)

        # commit the transaction
        conn.commit()
        response = {'status': StatusCodes['success'], 'results': f'Inserted users {payload["username"]}'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /users - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

## THIS IS AN EXAMPLE BELOW.

##
## Demo PUT
##
## Update a user based on a JSON payload
##
## To use it, you need to use postman or curl:
##
## curl -X PUT http://localhost:8080/users/ssmith -H 'Content-Type: application/json' -d '{"city": "Raleigh"}'
##

@app.route('/users/<username>', methods=['PUT'])
def update_users(username):
    logger.info('PUT /users/<username>')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'PUT /users/<username> - payload: {payload}')

    # do not forget to validate every argument, e.g.,:
    if 'city' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'city is required to update'}
        return flask.jsonify(response)

    # parameterized queries, good for security and performance
    statement = 'UPDATE auction SET minprice = %s AND auctionenddate = %s AND title = %s WHERE username = %s'
    values = (payload['city'], username)

    try:
        res = cur.execute(statement, values)
        response = {'status': StatusCodes['success'], 'results': f'Updated: {cur.rowcount}'}

        # commit the transaction
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)



# DO NOT CHANGE ANYTHING BELOW THIS COMMENT!

##########################################################
## MAIN
##########################################################
if __name__ == "__main__":

    # Set up the logging
    logging.basicConfig(filename="logs/log_file.log")
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    time.sleep(1) # just to let the DB start before this print :-)

    logger.info("\n---------------------------------------------------------------\n" + 
                  "API v1.1 online: http://localhost:8080/users/\n\n")

    app.run(host="0.0.0.0", debug=True, threaded=True)



