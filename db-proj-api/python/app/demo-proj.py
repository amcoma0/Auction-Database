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
## (insert description of function)
##
## (insert how to run function)

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
## (insert description of function)
##
## (insert how to test/run function)

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

    cur.execute('SELECT personid FROM users WHERE current_user = users.username ')
    userid = cur.fetchone

    # parameterized queries, good for security and performance
    statement = 'INSERT INTO auction (minprice, auctionenddate, title, description, item_itemid, seller_users_personid) \
    VALUES (%s, %s, %s, %s, %s, %s)'
    values = (payload['minprice'], payload['auctionenddate'], payload['title'],
              payload['description'],payload['item_itemid'], userid)

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


## List all existing auctions. (complete) *just need to add the token verification*
##
## This function lists all the existing auctions in the auctions table.
##
## curl -X GET http://localhost:8080/auctions -H "Content-Type: application/json" -H "access-token: ssmith513580758"

@app.route("/auctions", methods=['GET'])
@token_required
def get_all_auctions(current_user):
    logger.info("###   DEMO: GET /auctions   ###")

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT auctionid, item_itemid FROM auction")
    rows = cur.fetchall()

    payload = []
    logger.info("---- auctions  ----")
    for row in rows:
        logger.info(row)
        content = {'auctionid':int(row[0]), 'item_itemid':row[1]}
        payload.append(content) # payload to be returned

    conn.close()

    return flask.jsonify(payload)



## Search existing auctions.
##
## This function searches the available auctions with the keyword that relates to one or multiple auctions
##
## Use postman or cURL

@app.route("/dbproj/auctions/<keyword>/", methods=['GET'])
def search_auctions(keyword):
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
## (insert description of function)
##
## (insert how to test/run function)



## List all auctions in which the user has activity. (Not complete)
##
## (insert description of function)
##
## (insert how to test/run function)

@app.route("/userAuctions", methods=['GET'])
# We need to add token verification and uncomment the line below and make sure the function still works.
#@token_required
def get_all_userAuctions(): #(current_user): <-- Add this back to the "get_all_auctions" part when token verification is working.
    logger.info("###   DEMO: GET /userAuctions   ###")

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT auctionid, item_itemid FROM auction WHERE ") #Pick back up here Ramone.
    rows = cur.fetchall()

    payload = []
    logger.info("---- auctions  ----")
    for row in rows:
        logger.info(row)
        content = {'auctionid':int(row[0]), 'item_itemid':row[1]}
        payload.append(content) # payload to be returned

    conn.close()

    return flask.jsonify(payload)


## Place a bid in an auction.
##
## (insert description of function)
##
## (insert how to test/run function)

@app.route('/dbproj/bid/{auctionid}/{bid}/', methods=['POST'])
@token_required
def place_bid(auctionid, bid, current_user):
    logger.info('POST /bid')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'POST /bid - payload: {payload}')

    # do not forget to validate every argument, e.g.,:
    if 'username' not in payload or 'amount' not in payload or 'bid' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'value not in payload'}
        return flask.jsonify(response)

    cur.execute("SELECT auctionenddate FROM auction WHERE auctionid = auction.auctionid")
    auctionenddate = cur.fetchone()

    if datetime.date.today() > auctionenddate:
        response = {'status': StatusCodes['api_error'], 'results': 'Auction has already ended'}
        return flask.jsonify(response)

    cur.execute("SELECT minprice FROM auction WHERE auctionid = auction.auctionid")
    minprice = cur.fetchone()

    if bid < minprice:
        response = {'status': StatusCodes['api_error'], 'results': 'You must bid more than the minimum price'}
        return flask.jsonify(response)

    # parameterized queries, good for security and performance
    statement = 'INSERT INTO bids (amount, auction_auctionid, buyer_users_personid) VALUES (%s, %s, %s)'
    values = (bid, auctionid, current_user.personid)

    try:
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



## Write a message on the auction's board. (complete) 
##
## This function adds a message to the board table.
##
## Use postman.

@app.route('/messageBoard', methods=['POST'])
def add_messageBoard():
    logger.info('POST /messageBoard')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'POST /users - payload: {payload}')

    # do not forget to validate every argument, e.g.,:
    if 'message' not in payload or 'posttime' not in payload or 'auction_auctionid' not in payload or 'users_personid' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'Missing inputs.'}
        return flask.jsonify(response)

    # parameterized queries, good for security and performance
    statement = 'INSERT INTO board (message, posttime, auction_auctionid, users_personid) VALUES (%s, %s, %s, %s)'
    values = (payload['message'], payload['posttime'], payload['auction_auctionid'], payload['users_personid'])

    try:
        cur.execute(statement, values)

        # commit the transaction
        conn.commit()
        response = {'status': StatusCodes['success'], 'results': f'Inserted message {payload["message"]}'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /users - error: {error}')
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
# @app.route('/inbox', methods=['PUT'])
# def


## Outbid notification.
##
## (insert description of function)
##
## (insert how to test/run function)



## Close auction.
##
## (insert description of function)
##
## (insert how to test/run function)



## Cancel an auction.
##
## (insert description of function)
##
## (insert how to test/run function)



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
    statement = 'UPDATE users1 SET city = %s WHERE username = %s'
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



