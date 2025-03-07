try:
    import jwt
except Exception:
    import warnings
    warnings.warn(
        'PyJWT is not installed; JWT authentication is disabled',
        ImportWarning
    )
    jwt = None
from flask import request

__all__ = ['get_jwt']


def get_jwt(jwt_name='token', decoded=False, algorithms=['HS512']):
    if jwt is None:
        return None

    token = None
    try:
        if request.method in ['GET']:
            # Check the request args
            token = request.args.get(jwt_name, None)
        else:
            try:
                # Check for json first
                token = request.json.get(jwt_name, None)
            except Exception:
                token = None
            if token is None:
                try:
                    # Check for form data
                    token = request.form.get(jwt_name, None)
                except Exception:
                    token = None
            if token is None:
                try:
                    # Check the request args
                    token = request.args.get(jwt_name, None)
                except Exception:
                    token = None
    except Exception:
        token = None

    if token is None:
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
