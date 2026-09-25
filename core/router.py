import re
from urllib.parse import parse_qs, urlparse

from pyrogram.errors import RPCError


class Router:
    def __init__(self):
        self.routes = []

    def add_route(self, path_pattern, handler_class, handler_method):
        param_pattern = re.compile(r"<(\w+)>")
        param_names = param_pattern.findall(path_pattern)
        route_pattern = param_pattern.sub(r"(?P<\1>[^/]+)", path_pattern)
        path_regex = re.compile(f"^{route_pattern}$")
        self.routes.append((path_regex, param_names, handler_class, handler_method))

    async def route(self, url, *args, **kwargs):
        parsed_url = urlparse(url)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        for path_regex, param_names, handler_class, handler_method in self.routes:
            match = path_regex.match(path)
            if not match:
                continue

            for param_name in param_names:
                query_params[param_name] = match.group(param_name)

            try:
                handler = handler_class(*args, **kwargs)
                return await getattr(handler, handler_method)(**query_params)
            except (RPCError, Exception) as err:
                raise ValueError(f"路由执行 {handler_method} 方法错误:{err}") from err

        raise ValueError("开发中-导航页面不存在")
