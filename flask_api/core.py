from flask import Flask, after_this_request
from collections import defaultdict
from functools import wraps
from .blueprints import ApiBlueprint, use_api_errors
from .responses import ApiResult, ApiException, ApiFileResult


class FlaskApi:
    serializer = None
    csrf_protect = True

    def Blueprint(self, *args, **kwargs):
        return ApiBlueprint(*args, api_instance=self, **kwargs)

    class Result(ApiResult):
        pass

    class Exception(ApiException):
        pass

    class FileResult(ApiFileResult):
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

        @self._app.errorhandler(ApiException)
        def err_api(error):
            return error.to_response(serializer=self.serializer)

        self._create_generic_api_routes()

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

    def _create_generic_api_routes(self):
        @self._app.route("/api/")
        def api_map():
            try:
                api_urls = defaultdict(dict)
                for rule in self._app.url_map.iter_rules():
                    url = rule.rule
                    if not url.startswith('/api'):
                        continue
                    if rule.endpoint.endswith('404'):
                        continue
                    if rule.endpoint.endswith('_redirect'):
                        continue
                    if url.startswith('/api/hidden'):
                        continue
                    endpoint = rule.endpoint.split('.', 1)
                    if len(endpoint) == 1:
                        api_urls[rule.endpoint] = {
                            'url': url,
                            'methods': list(rule.methods)
                        }
                    else:
                        api_urls[endpoint[0]][endpoint[1]] = {
                            'url': url,
                            'methods': list(rule.methods)
                        }
                return self.Result({'endpoints': api_urls})
            except Exception as e:
                return self.Exception(str(e))

        @self._app.route("/api/<path:dummy>/")
        def api_404(dummy=None):
            raise self.Exception('Not Found', 404)

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
