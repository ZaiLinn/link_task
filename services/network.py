import requests

from public.logger import LoggerConfig


network_logs = LoggerConfig("network", "logs/network.log").get_logger()


def addressNetwork(ip=None):
    url = "http://ip-api.com/json/"
    if ip:
        url = f"http://ip-api.com/json/{ip}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json().get("query")
    except Exception as err:
        network_logs.error(f"公网地址检测失败:{err}")
    return None
