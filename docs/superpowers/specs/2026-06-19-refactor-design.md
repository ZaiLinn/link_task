# 重构设计文档

**日期:** 2026-06-19  
**项目:** link_task（Telegram 任务推广机器人）  
**方案:** 方案 B — 分层重构

---

## 背景

link_task 是一个基于 Pyrogram 的 Telegram 机器人，提供任务推广平台：商家发布拉人入群任务，用户完成任务赚佣金。现有代码存在三个核心问题：

1. **安全性**：`config.py` 中硬编码了 MySQL 密码、Redis 连接、Bot Token、OkPay Token 等敏感信息
2. **可维护性**：`public/method.py`（639行）混杂了路由类、认证类、业务逻辑、定时任务、工具函数；`views/client/index.py` 的 `Index` 类重复实现了 `BaseView` 已有的方法
3. **可扩展性**：数据访问代码散落在 `views/*/date.py` 各处，没有统一的数据层；业务逻辑与 Telegram 事件处理耦合在一起

---

## 目标

- 将所有密钥/连接信息移到 `.env` 文件，不提交到版本控制
- 按职责分层：基础设施（core）/ 业务逻辑（services）/ 事件处理（handlers）/ 视图（views）/ 数据访问（data）
- 消除 `public/method.py` 这个"杂物抽屉"，各模块职责清晰
- 修复 `Index` 类不继承 `BaseView` 的问题
- 不改变任何业务逻辑，保持现有功能完全不变

---

## 目标目录结构

```
link_task/
├── .env                    ← 密钥/连接串（不提交）
├── .env.example            ← 模板（提交）
├── main.py                 ← 只负责启动
│
├── core/
│   ├── __init__.py
│   ├── config.py           ← 从 .env 加载配置，替代原 config.py
│   ├── bot.py              ← Pyrogram Client 单例
│   ├── database.py         ← Card 类（DB 连接池单例）
│   ├── redis_client.py     ← Redis 单例
│   ├── cache.py            ← Var 类（Redis KV 临时存储）
│   ├── scheduler.py        ← APScheduler 单例
│   ├── router.py           ← Router 类
│   └── auth.py             ← UserAuth、RestrictAccess
│
├── services/
│   ├── __init__.py
│   ├── settlement.py       ← SettlementTime、AutomaticDettlementTime、辅助函数
│   ├── task_push.py        ← TaskSendMsg、get_task_text
│   ├── task_operation.py   ← TaskOperation 类
│   ├── group_member.py     ← BorInGroup 类
│   └── payment.py          ← OkayPay 类
│
├── handlers/
│   ├── __init__.py
│   ├── commands.py         ← 原 monitor/command.py
│   ├── input.py            ← 原 monitor/input.py
│   └── setup.py            ← command()、admin_command() 注册函数（原 main.py）
│
├── data/
│   ├── __init__.py
│   ├── user.py             ← ChatUser 类
│   ├── config_data.py      ← ConfigData 类
│   ├── task.py             ← TaskDate、MyTaskDate、MySettlementDate 等
│   ├── settlement.py       ← SettlementTimeDate、AutomaticDettlementTimeDate 等
│   ├── wallet.py           ← TopUpOrder、MyWalletDate、MerchantWallet 相关
│   └── group.py            ← BorInGroupData、TaskSendMsgData 等
│
├── views/
│   ├── base.py             ← BaseView（不变）
│   ├── client/
│   │   ├── index.py        ← Index 改继承 BaseView，删重复 sendMsg/retChat
│   │   ├── task.py
│   │   └── publish.py
│   └── admin/
│       ├── index.py
│       ├── settlement.py
│       ├── user.py
│       ├── wallet.py
│       └── withdraw.py
│
├── public/
│   ├── logger.py           ← 不变
│   ├── date.py             ← 不变（datetime 工具函数）
│   ├── utils.py            ← truncate_string、msgNotify、isPrivileges、addressNetwork
│   └── web.py              ← 支付回调 HTTP 服务（aiohttp）
│
└── router.py               ← 路由注册表（不变，引用 core/router.py 的 Router）
```

---

## 各层职责

### core/ — 基础设施层

每个文件提供一个全局单例，供其他层导入使用。

- **config.py**: 用 `python-dotenv` 读取 `.env`，构建 `mysql_config` dict、`bot_config` dict、`cli_obj` dict。提供 `get_config()` 函数（从 DB 加载运行时配置）。原 `config.py` 的全部逻辑移入此处，密钥改从环境变量读取。
- **database.py**: `Card` 类从 `data/data.py` 移入，`db` 单例在此创建。
- **redis_client.py**: `redis_client` 单例在此创建。
- **bot.py**: `app`（Pyrogram Client）单例在此创建，引用 `core/config.py` 的配置。
- **scheduler.py**: `scheduler`（AsyncIOScheduler）单例。
- **router.py**: `Router` 类从 `public/method.py` 移入。
- **auth.py**: `UserAuth`、`RestrictAccess` 从 `public/method.py` 移入。

### services/ — 业务逻辑层

纯业务逻辑，不直接处理 Telegram 消息格式，只调用 `data/` 和 `core/bot.py`。

- **settlement.py**: `SettlementTime`、`AutomaticDettlementTime`、`CheckBillingInvited`、`StatisticalSuccessRate`
- **task_push.py**: `TaskSendMsg`、`get_task_text`
- **task_operation.py**: `TaskOperation` 类（任务上线/下线）
- **group_member.py**: `BorInGroup` 类（用户入群/退群检测、作弊检测）
- **payment.py**: `OkayPay` 类

### handlers/ — 事件处理层

只负责接收 Telegram 事件，做权限/频率检查，然后委托给 views 或 services。

- **commands.py**: 原 `monitor/command.py` 内容
- **input.py**: 原 `monitor/input.py` 内容
- **setup.py**: `command()`、`admin_command()` 函数，在 `main.py` 中调用

### data/ — 数据访问层

所有 SQL 操作集中于此。每个文件对应一个业务域，类的命名去掉 "Date" 后缀（原命名如 `TaskDate` 是历史遗留，含义不明确），改为 `TaskRepository`、`SettlementRepository` 等，或保持现有命名以降低迁移风险（优先选后者）。

现有 `views/*/date.py` 中的所有 DB 类移入 `data/` 对应文件，`views/*/date.py` 文件删除。

### views/ — 视图层

只负责组装 Telegram 消息文本和键盘，调用 `data/` 查询数据。

**关键修复**：`views/client/index.py` 的 `Index` 类目前自己实现了 `sendMsg` 和 `retChat`，与 `BaseView` 重复。改为继承 `BaseView`，删除重复代码（约20行）。

### public/ — 工具层

- **utils.py**: `truncate_string`、`msgNotify`、`isPrivileges`、`addressNetwork`（从 `public/method.py` 保留的工具函数）
- **method.py**: 文件删除，内容已分散到各层
- **web.py**: 不变

---

## .env 文件设计

```env
# MySQL
MYSQL_HOST=104.156.244.176
MYSQL_PORT=3307
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=link_task
MYSQL_POOL_SIZE=10

# Redis
REDIS_HOST=104.156.244.176
REDIS_PORT=8800
REDIS_DB=10

# Pyrogram Bot
BOT_NAME=LinkTaskBot
BOT_API_ID=26614768
BOT_API_HASH=your_api_hash_here
BOT_TOKEN=your_bot_token_here

# OkPay
OKPAY_ID=1912
OKPAY_TOKEN=your_okpay_token_here
```

---

## 迁移顺序

重构分7步，每步独立可验证，不影响运行中的功能：

1. **添加 .env + core/config.py** — 最高优先级，解决安全问题
2. **拆分 core/ 基础设施** — database、redis_client、bot、scheduler、router、auth
3. **建立 data/ 数据层** — 将 views/*/date.py 的类迁移过来
4. **建立 services/ 业务层** — 从 public/method.py 提取业务类/函数
5. **重构 handlers/** — monitor/ 改名，setup.py 从 main.py 提取
6. **修复 views/client/index.py** — Index 继承 BaseView
7. **清理** — 删除 public/method.py、views/*/date.py、data/data.py、旧 config.py

---

## 不在本次范围内

- 异步数据库（aiomysql）— 风险高，单独立项
- 类型注解 / dataclass 替代裸元组 — 单独立项
- 测试覆盖 — 单独立项
- `requirements.txt` 依赖版本升级

---

## 验收标准

- `python main.py` 能正常启动，Bot 响应 `/start` 命令
- `.env` 文件不被提交到版本控制（`.gitignore` 中包含）
- `public/method.py` 文件不存在
- `views/client/index.py` 的 `Index` 类继承 `BaseView`，无重复 `sendMsg`/`retChat`
- `data/` 目录包含所有数据访问类，`views/*/date.py` 文件不存在
