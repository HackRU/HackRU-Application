from datetime import datetime

from testing_utils import *
import authorize
import validate
import config

import pytest
import json

@pytest.mark.run(order=3)
def test_validate_token():
    user_email = "creep@radiohead.ed"
    passwd = "love"
    usr_dict = {'email': user_email, 'password': passwd}
    auth = authorize.authorize(usr_dict, None)
    token = json.loads(auth['body'])['auth']['token']

    #make sure user exists
    user_dict = get_db_user(user_email)
    assert 'email' in user_dict and user_dict['email'] == user_email

    #success
    val = validate.validate({'email': user_email, 'token': token}, None)
    assert check_by_schema(schema_for_http(200, {"type": "object", "const": user_dict}), val)

    #failures
    val = validate.validate({'email': user_email + 'fl', 'token': token}, None)
    assert check_by_schema(schema_for_http(403, {"type": "string", "const": "User not found"}), val)
    val = validate.validate({'email': user_email, 'token': token + 'fl'}, None)
    assert check_by_schema(schema_for_http(403, {"type": "string", "const": "Token invalid"}), val)
    val = validate.validate({'emil': user_email, 'token': token + 'fl'}, None)
    assert check_by_schema(schema_for_http(403, {"type": "string"}), val)
    val = validate.validate({'email': user_email, 'oken': token + 'fl'}, None)
    assert check_by_schema(schema_for_http(403, {"type": "string"}), val)

    #insert expired token
    expired = 'fish'
    users = connect_to_db()
    users.update_one({'email': user_email},{'$push': {'auth': {
        'token': expired,
        'valid_until': datetime.now().isoformat()
    }}})

    val = validate.validate({'email': user_email, 'token': expired}, None)
    assert check_by_schema(schema_for_http(403, {"type": "string", "const": "Token invalid"}), val)
    
    # remove the token
    users.update_one({'email': user_email},{'$pull': {'auth': {'token': expired}}})
