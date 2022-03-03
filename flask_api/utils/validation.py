import jwt
from flask import request

__all__ = ['get_jwt']


def get_jwt(jwt_name='token', decoded=False, algorithms=['HS512']):

    token = None
    try:
        if request.method in ['POST', 'PATCH']:
            # Check for json
            token = request.json.get(jwt_name, None)
        elif request.method in ['GET']:
            # Check the request args
            token = request.args.get(jwt_name, None)
    except Exception:
        return None

    if not decoded:
        return token

    try:
        return jwt.decode(
            token, algorithms=algorithms,
            options={"verify_signature": False}
        )
    except Exception:
        return None
