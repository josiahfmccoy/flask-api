import json
import os
from collections import defaultdict
from .responses import ApiResult, ApiException, job_path

__all__ = ['create_generic_api_routes']


def create_generic_api_routes(api, app):
    @app.errorhandler(ApiException)
    def err_api(error):
        return error.to_response(serializer=api.serializer)

        @app.route("/api/")
        def api_map():
            try:
                api_urls = defaultdict(dict)
                for rule in app.url_map.iter_rules():
                    url = rule.rule
                    if not url.startswith('/api'):
                        continue
                    if rule.endpoint.endswith('404'):
                        continue
                    if rule.endpoint.endswith('_redirect'):
                        continue
                    for h in api.hidden_routes:
                        if url.startswith(h):
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
                return ApiResult({'endpoints': api_urls})
            except Exception as e:
                return ApiException(str(e))

        @app.route('/api/job/<string:job_id>', methods=['GET'])
        def check_job(job_id):
            app.logger.debug(f'Checking for job {job_id} ...')
            try:
                fpath = job_path(job_id)
                with open(fpath, 'r') as f:
                    data = json.load(f)
            except FileNotFoundError:
                return ApiResult({'status': 'pending'})

            try:
                os.remove(fpath)
            except Exception:
                pass

            return ApiResult(data)

        @app.route("/api/<path:dummy>/")
        def api_404(dummy=None, methods=[
            'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'
        ]):
            raise ApiException('Not Found', 404)
