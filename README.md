# LinkTask Bot

基于 [Pyrogram](https://github.com/pyrogram/pyrogram) 的 Telegram 任务推广机器人。商家发布入群任务，用户完成任务赚取佣金，支持 OkPay 自动充值与结算。

---

## 功能

- **商家端**：发布入群推广任务、设置单价与人数上限、管理任务上下线、查看结算记录
- **用户端**：领取任务、生成专属推广链接、查看收益与提现记录
- **管理端**：用户管理、结算审核、充值流水、机器人参数配置
- **支付**：OkPay 回调自动充值，支持 USDT
- **自动结算**：每日定时触发，检测用户入群状态，疑似作弊自动拒绝
- **限流**：Redis 频率限制，防刷接口

---

## 技术栈

| 组件 | 版本 |
|---|---|
| Python | 3.14+ |
| Pyrogram | 2.0.106 |
| MySQL | 8.0+ |
| Redis | 7+ |
| APScheduler | 3.x |
| aiohttp | 3.x |

---

## 目录结构

```
link_task/
├── main.py                 # 启动入口
├── router.py               # 路由注册表
├── config.py               # 向后兼容 shim（勿直接修改）
│
├── core/                   # 基础设施单例
│   ├── config.py           # 从 .env 读取配置
│   ├── bot.py              # Pyrogram Client
│   ├── redis_client.py     # Redis 连接
│   ├── scheduler.py        # APScheduler
│   ├── router.py           # Router 类
│   └── auth.py             # UserAuth、RestrictAccess
│
├── services/               # 业务逻辑
│   ├── settlement.py       # 自动结算（并发处理）
│   ├── payment.py          # OkPay 支付
│   ├── task_broadcast.py   # 任务广播
│   ├── group_membership.py # 入群/退群检测
│   └── ...
│
├── handlers/               # Telegram 事件处理
│   ├── commands.py         # 命令路由
│   ├── input.py            # 文本输入路由
│   └── setup.py            # 注册所有 Handler
│
├── repositories/           # 数据访问层（SQL）
│   ├── admin/
│   └── client/
│
├── views/                  # 消息组装与键盘
│   ├── base.py
│   ├── admin/
│   └── client/
│
├── data/
│   └── data.py             # DB 连接池 + ChatUser + ConfigData
│
├── public/
│   ├── web.py              # OkPay 回调 HTTP 服务（aiohttp）
│   ├── logger.py           # 日志配置
│   └── security.py         # 敏感配置脱敏
│
├── migrations/
│   └── 20260703_security_indexes.sql
│
├── .env.example            # 环境变量模板
├── Dockerfile
└── requirements.txt
```

---

## 快速开始

### 1. 克隆并安装依赖

```bash
git clone https://github.com/yourname/link_task.git
cd link_task
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填写以下必填项：

| 变量 | 说明 |
|---|---|
| `MYSQL_HOST` / `MYSQL_PORT` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DATABASE` | MySQL 连接信息 |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` | Redis 连接信息 |
| `BOT_API_ID` / `BOT_API_HASH` | 从 [my.telegram.org](https://my.telegram.org) 获取 |
| `BOT_TOKEN` | 从 [@BotFather](https://t.me/BotFather) 获取 |
| `OKPAY_ID` / `OKPAY_TOKEN` | OkPay 商户 ID 和 Token |
| `CALLBACK_ADDRESS` | OkPay 回调公网地址，例如 `http://1.2.3.4:8888/okPay` |

### 3. 初始化数据库

创建数据库后，执行建表 SQL（表结构文件需自行维护或由运维提供），然后执行索引迁移：

```bash
mysql -u root -p link_task < migrations/20260703_security_indexes.sql
```

### 4. 启动

```bash
python main.py
```

---

## Docker 部署

```bash
# 构建镜像
docker build -t link_task .

# 运行（挂载 .env 文件）
docker run -d \
  --name link_task \
  --env-file .env \
  -p 8888:8888 \
  link_task
```

> OkPay 回调端口默认 8888，确保防火墙已开放，并在 `.env` 中将 `CALLBACK_ADDRESS` 设为公网地址。

---

## 代理配置（可选）

如需通过 SOCKS5 代理访问 Telegram：

```env
BOT_PROXY=true
BOT_PROXY_SCHEME=socks5
BOT_PROXY_HOST=127.0.0.1
BOT_PROXY_PORT=1080
```

---

## Session 登录（可选）

如需使用 session string 而非 bot token 启动：

```env
BOT_SESSION=true
BOT_SESSION_FILE=session.txt
```

将 session string 写入 `session.txt` 即可。

---

## 定时任务

| 任务 | 触发时机 | 说明 |
|---|---|---|
| 自动结算 | 每天 00:05 | 处理前一天到期结算，检测用户在群状态 |
| 任务广播 | 每小时 | 向用户推送待领取任务消息 |

---

## 路由规范

`router.py` 使用中文路径注册所有回调路由：

- `r/` 前缀：普通用户路由
- `a/` 前缀：管理员路由

示例：

```python
router.add_route('r/任务首页', TaskIndex, 'index')
router.add_route('a/管理首页', Admin, 'index')
```

---

## 安全说明

- 所有密钥通过 `.env` 注入，不提交到版本控制（`.gitignore` 已配置）
- OkPay 回调验签使用 HMAC，防重放攻击使用 Redis 幂等锁
- `order_id` 使用 `uuid4().hex` 生成，避免并发碰撞
- 运行日志中敏感字段自动脱敏（见 `public/security.py`）

---

## 依赖

```
aiohttp>=3.12,<4
APScheduler>=3.11,<4
emoji>=2.14,<3
mysql-connector-python>=9.3,<10
Pillow>=11.3,<12
Pyrogram==2.0.106
PySocks>=1.7,<2
qrcode>=8.2,<9
redis>=6.2,<7
requests>=2.32,<3
```

---

## License

MIT
