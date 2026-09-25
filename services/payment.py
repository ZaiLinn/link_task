import asyncio
import requests
from core.config import bot_config
from services.okpay_callback import _okpay_md5


class OkayPay:
    def __init__(self):
        self.id = bot_config['OkPay_id']
        self.token = bot_config['OkPay_token']
        api_url = 'https://okpay.xgram.me/shop/'
        self.api_url_payLink = api_url + 'payLink'
        self.api_url_transfer = api_url + 'transfer'
        self.api_url_censorUserByTG = api_url + 'censorUserByTG'
        self.api_url_TransactionHistory = api_url + 'TransactionHistory'

    async def pay_link(self, data):
        return await self._post(self.api_url_payLink, data)

    async def transfer(self, data):
        return await self._post(self.api_url_transfer, data)

    async def censorUserByTG(self, data):
        return await self._post(self.api_url_censorUserByTG, data)

    def sign(self, data):
        data = {k: v for k, v in data.items() if v is not None}
        data["id"] = self.id
        data["sign"] = _okpay_md5(data, self.id, self.token)
        return data

    async def _post(self, url, data):
        data = self.sign(data)
        response = await asyncio.to_thread(requests.post, url, data=data, timeout=10)
        return response.json()
