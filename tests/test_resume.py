from testing_utils import *
from src import authorize, util, resume
import config
import json

import requests

email = "test@t.t"
pword = "jjjjjjjf"
token = ""
old_col = ""


def setup_module(m):
    # temp change user collection
    global old_col
    old_col = config.DB_COLLECTIONS["users"]
    config.DB_COLLECTIONS["users"] = "test-users"

    # create a user
    result = authorize.create_user({'body': json.dumps({"email": email, "password": pword})}, {})
    assert result["statusCode"] == 200
    global token
    token = json.loads(result["body"])["token"]


def teardown_module(m):
    # drop temp collection
    db = util.get_db()
    db[config.DB_COLLECTIONS["users"]].drop()

    # reset colelction name
    global old_col
    config.DB_COLLECTIONS["users"] = old_col


def test_baduser():
    result = resume.resume({'body': json.dumps({"token": token + "bad"})}, {})
    assert result["statusCode"] == 403


def test_roundtrip():
    result = resume.resume({'body': json.dumps({"token": token})}, {})
    assert result["statusCode"] == 200
    upload = json.loads(result["body"])["upload"]
    download = json.loads(result["body"])["download"]
    
    stellar_resume = b'hire me plz'
    upload_res = requests.put(upload, data=stellar_resume, headers={"Content-Type": "application/pdf"})
    assert upload_res.status_code == 200 or upload_res.status_code == 204

    download_res = requests.get(download)
    assert download_res.status_code == 200
    assert download_res.content == stellar_resume

    result = resume.resume({'body': json.dumps({"token": token})}, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"])["exists"]


def test_exists():
    """check using an email that wasn't uploaded"""
    creation = authorize.create_user({'body': json.dumps({"email": email + "d", "password": pword})}, {})
    assert creation["statusCode"] == 200
    token = json.loads(creation["body"])["token"]

    
    result = resume.resume({'body': json.dumps({"token": token})}, {})
    assert result["statusCode"] == 200
    assert not json.loads(result["body"])["exists"]
