import uuid
import json

from aiohttp import web
from pyrogram.errors import RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import datetime
from core.bot import app as bot_app
from core.redis_client import redis_client
from public.logger import LoggerConfig
from services.okpay_callback import verify_callback_token, verify_okpay_signature
from services.topup_order import TopUpOrder

logs=LoggerConfig('pay', 'logs/main.log').get_logger()

async def okPay_order(post_json):
    logs.critical(f"okPay充值回调:{post_json}")
    # okpay充值
    TUP = TopUpOrder()
    try:
        if post_json.get('code') == 200 and post_json.get('status') == "success":
            res_order = post_json.get('data')
            if not isinstance(res_order, dict):
                logs.error("OkPay充值回调缺少data")
                return
            lock_key = f"okpay:callback:{res_order.get('unique_id')}:{res_order.get('order_id')}"
            if not redis_client.set(lock_key, "1", ex=300, nx=True):
                logs.critical(f"OkPay重复回调已忽略:{lock_key}")
                return
            result = await TUP.confirm_okpay_order(
                order_id=res_order.get('unique_id'),
                transaction_id=res_order.get('order_id'),
                amount=res_order.get('amount'),
                pay_time=datetime.datetime.now(),
                ledger_order_id=uuid.uuid4().hex,
            )
            if result.get('status') == 'success':
                text = f"💳 充值成功 {result['price']} USDT\n\n" \
                       f"充值前余额:{result['before_balance']}\n" \
                       f"当前余额:{result['balance']}\n" \
                       f"请返回钱包查看充值详情"
                keyword = [[InlineKeyboardButton(f"↩️ 返回钱包", callback_data="r/商家钱包?state=0")]]
                await bot_app.send_message(chat_id=res_order.get('pay_user_id'), text=text,
                                 reply_markup=InlineKeyboardMarkup(keyword))
            elif result.get('status') == 'amount_mismatch':
                logs.error(f"OkPay充值金额不一致: callback={res_order.get('amount')}, order={result.get('order_price')}")
            elif result.get('status') == 'error':
                logs.error(f"OkPay入账事务失败:{result.get('error')}")
                redis_client.delete(lock_key)
            else:
                logs.critical(f"OkPay订单不存在或已处理:{res_order.get('unique_id')}/{res_order.get('order_id')} status={result.get('status')}")
    except (Exception,RPCError) as e:
        logs.error(f'充值失败{e}')
async def handle_post(request):
    post_data = await request.read()
    headers = {'Content-type': 'text/html'}
    try:
        post_json=json.loads(post_data)
        if not (verify_okpay_signature(post_json) or verify_callback_token(request)):
            logs.error("OkPay回调验证失败")
            return web.json_response({'error': 'Forbidden'}, status=403)
        await okPay_order(post_json=post_json)
    except Exception as e:
        logs.error(f"/okPay:{e}")
        return web.json_response({'error': 'Server error'}, status=500)
    return web.Response(text='200', headers=headers)
async def not_found(request):
    return web.Response(text="404 Not Found", status=404)

async def start_server():
    try:
        app = web.Application()
        app.router.add_post('/okPay', handle_post)  # 添加 POST 请求路由
        app.router.add_route('*', '/{tail:.*}', not_found)  # 处理所有未匹配路由的情况，返回404
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host='0.0.0.0', port=8888)

        logs.critical(f"Web 服务启动成功 {await site.start()}")
    except Exception as e:
        logs.critical(f"Web 服务失败,{e}")
