import asyncio
import hashlib
import requests
from core.config import bot_config


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
        data['id'] = self.id
        data = {k: v for k, v in data.items() if v is not None}
        data = dict(sorted(data.items()))
        sign_str = '&'.join([f"{k}={v}" for k, v in data.items()]) + f'&token={self.token}'
        data['sign'] = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
        return data

    async def _post(self, url, data):
        data = self.sign(data)
        response = await asyncio.to_thread(requests.post, url, data=data, timeout=10)
        return response.json()
