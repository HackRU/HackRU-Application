import jsonschema as js
import config

from pymongo import MongoClient
import dateutil.parser as dp

from functools import wraps
from datetime import datetime

def ensure_schema(schema):
    js.Draft4Validator.check_schema(schema)
    def wrap(fn):
        @wraps(fn)
        def wrapt(event, context, *extras):
            try:
                js.validate(event, schema)
                return config.add_cors_headers(fn(event, context, *extras))
            except js.exceptions.ValidationError as e:
                return config.add_cors_headers({"statusCode": 400, "body": "Error in JSON: {}".format(e)})
        return wrapt
    return wrap

def ensure_logged_in_user(email_key='email', token_key='token'):
    def rapper(fn):
        @wraps(fn)
        def wrapt(event, context, *args):
            email = event[email_key]
            token = event[token_key]

            #connect to DB
            client = MongoClient(config.DB_URI)
            db = client[config.DB_NAME]
            db.authenticate(config.DB_USER, config.DB_PASS)

            tests = db[config.DB_COLLECTIONS['users']]

            #try to find our user
            results = tests.find_one({"email":email})
            if results == None or results == [] or results == ():
                return {"statusCode": 400, "body": "User not found"}

            #if none of the user's unexpired tokens match the one given, complain.
            if not any(i['token'] == token and datetime.now() < dp.parse(i['valid_until']) for i in results['auth']):
                return {"statusCode": 400, "body": "Token not found"}

            return fn(event, context, results, *args)
        return wrapt
    return rapper

def ensure_role(roles):
    def ensure_auth_user(fn):
        @wraps(fn)
        def wrapt(event, context, user, *args):
            if all(any(user['role'].get(role, False) for role in options) for options in roles):
                return fn(event, context, user, *args)
            return {"statusCode": 403, "body": "User does not have priviledges."}
        return wrapt
    return ensure_auth_user
