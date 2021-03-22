from flask import Flask, after_this_request
from functools import wraps
from .blueprints import ApiBlueprint, use_api_errors
from .responses import ApiResult, ApiException, ApiFileResult, ApiAsyncJob
from .routes import create_generic_api_routes


class FlaskApi:
    serializer = None
    csrf_protect = True

    hidden_routes = ['/api/hidden']

    def Blueprint(self, *args, **kwargs):
        return ApiBlueprint(*args, api_instance=self, **kwargs)

    class Result(ApiResult):
        pass

    class Exception(ApiException):
        pass

    class FileResult(ApiFileResult):
        pass

    class AsyncJob(ApiAsyncJob):
        pass

    def __init__(self, app=None, *args, **kwargs):
        if app:
            self.init_app(app, **kwargs)
        else:
            self._set_options(**kwargs)

    def _set_options(self, **options):
        self.serializer = options.pop(
            'default_serializer', self.serializer
        )

        self.csrf_protect = options.pop(
            'csrf_protect', self.csrf_protect
        )

    def init_app(self, app, **kwargs):
        self._app = app
        self._set_options(**kwargs)

        self._setup_csrf()

        def make_response(rv):
            if isinstance(rv, ApiResult):
                return rv.to_response(serializer=self.serializer)
            return Flask.make_response(app, rv)

        self._app.make_response = make_response

        create_generic_api_routes(self, self._app)

    def _setup_csrf(self):
        self._csrf = None
        self.csrf_exempt = lambda x: True
        if self.csrf_protect:
            try:
                from flask_wtf.csrf import CSRFProtect
                self._csrf = CSRFProtect()
                if self.csrf_protect:
                    self._csrf.init_app(self._app)
                    self.csrf_exempt = self._csrf.exempt
            except ImportError:
                self.csrf_protect = False

    def use_api_errors(self, blueprint):
        use_api_errors(self, blueprint)

    def validate(self, validator, **options):
        def decorated(f):
            @wraps(f)
            def validated(*args, **kwargs):
                validator(**options)
                return f(*args, **kwargs)
            if self.csrf_protect:
                return self.csrf_exempt(validated)
            else:
                return validated
        return decorated

    def encrypt_response(self, service, **options):
        def decorated(f):
            @wraps(f)
            def encrypted(*args, **kwargs):
                @after_this_request
                def encrypt_response(response):
                    service(response, **options)
                    return response
                return f(*args, **kwargs)
            return encrypted
        return decorated
