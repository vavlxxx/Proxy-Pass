import json
from pathlib import Path
from urllib.parse import urlencode, urljoin

from fastapi import Request

from src.caching_proxy.config import settings
from src.caching_proxy.schemas import AppConfig, AppStatus, RequestComponents


class CachingHelper:
    @staticmethod
    def extract_request_components(request: Request) -> RequestComponents:
        return RequestComponents(
            headers=CachingHelper.clean_request_headers(dict(request.headers)),
            params=dict(request.query_params),
            path=request.url.path.lstrip("/"),
            method=request.method,
        )

    @staticmethod
    def clean_request_headers(headers: dict) -> dict:
        return {k: v for k, v in headers.items() if k.lower() not in settings.REQUEST_EXCLUDED_HEADERS}

    @staticmethod
    def clean_response_headers_for_cache(headers: dict) -> dict:
        return {k: v for k, v in headers.items() if k.lower() not in settings.RESPONSE_EXCLUDED_HEADERS}

    @staticmethod
    def make_cache_key(request_components: RequestComponents) -> str:
        path_with_params = request_components.path

        if request_components.params:
            query_string = urlencode(sorted(request_components.params.items()))
            path_with_params = f"{path_with_params}?{query_string}"

        return f"{request_components.method} {path_with_params}"

    @staticmethod
    def make_absolute_url(base: str, path: str) -> str:
        return urljoin(base, path).rstrip("/")

    @staticmethod
    def join_host_and_port(host: str, port: int) -> str:
        return f"http://{host}:{port}"


class ConfigHelper:
    def __init__(self, cfg_file: Path):
        self._cfg_file = cfg_file

    def read_config(self) -> AppConfig:
        if not self._cfg_file.exists():
            return AppConfig(servers=[])

        try:
            json_string = self._cfg_file.read_text()
            data = json.loads(json_string)
            return AppConfig.model_validate(data)
        except Exception:
            return AppConfig(servers=[])

    def write_config(self, config: AppConfig):
        data = config.model_dump()
        json_string = json.dumps(data, indent=4)
        self._cfg_file.write_text(json_string)

    def add_server_to_config(self, server: AppStatus):
        config = self.read_config()
        config.servers = [serv for serv in config.servers if serv.port != server.port]
        config.servers.append(server)
        self.write_config(config)

    def remove_server_from_config(self, port: int):
        config = self.read_config()
        config.servers = [serv for serv in config.servers if serv.port != port]
        self.write_config(config)

    def get_server_by_port(self, port: int):
        config = self.read_config()
        for server in config.servers:
            if server.port == port:
                return server
        return None

    def get_last_server(self):
        config = self.read_config()
        if not config.servers:
            return None
        return config.servers[-1]


cfg = ConfigHelper(cfg_file=settings.APP_CONFIG_FILE)
