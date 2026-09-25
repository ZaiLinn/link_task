import os
from pyrogram import Client
from core.config import cli_obj


def _create_client(obj):
    if os.path.exists(obj["sessionTxt"]) and obj["session"]:
        with open(obj["sessionTxt"], "r") as f:
            content = f.read()
        if obj["proxy"]:
            return Client("HuTuiBot", session_string=content, proxy=obj["proxyDict"])
        return Client("HuTuiBot", session_string=content)
    if obj["proxy"]:
        return Client(
            obj["name"],
            api_id=obj["api_id"],
            api_hash=obj["api_hash"],
            bot_token=obj["bot_token"],
            proxy=obj["proxyDict"],
        )
    return Client(
        obj["name"],
        api_id=obj["api_id"],
        api_hash=obj["api_hash"],
        bot_token=obj["bot_token"],
    )


app = _create_client(cli_obj)
