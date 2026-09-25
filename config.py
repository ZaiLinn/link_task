# Backward-compat shim. New code: import from core.* directly.
import os, re, time, requests, json, asyncio, redis, qrcode, io, socket, hashlib, math, datetime
from random import randint

from pyrogram import Client, filters
from pyrogram.handlers import (
    CallbackQueryHandler,
    ChatJoinRequestHandler,
    ChatMemberUpdatedHandler,
    DisconnectHandler,
    MessageHandler,
)
from pyrogram.errors import RPCError, FloodWait, BadRequest, ChannelPrivate
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ForceReply,
    ReplyKeyboardMarkup, Message, ChatMemberUpdated, ChatJoinRequest,
    InputMediaVideo, InputMediaPhoto, MenuButton, BotCommand,
)
from urllib.parse import urlparse, parse_qs

from core.config import (
    mysql_config,
    redis_config,
    bot_config,
    cli_obj,
    refresh_secret_config_from_env,
)
from core.bot import app
from core.redis_client import redis_client
from core.scheduler import scheduler
