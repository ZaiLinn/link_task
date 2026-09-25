---
date: 2026-06-18
topic: BaseView 基类重构
status: approved
---

# BaseView 基类重构

## 问题

项目中 10 个视图类（TaskIndex、MyTask、MySettlement、MyWithdraw、MyWallet、PublishIndex、PublishPostTask、PublishList、Settlement、MerchantWallet、Admin）各自重复了相同的 `__init__`、`retChat`、`sendMsg` 三个方法，共约 300 行重复代码。

## 方案

新建 `views/base.py`，提取公共方法为 `BaseView` 基类，所有视图类继承它。

## 设计

### views/base.py

```python
class BaseView:
    def __init__(self, Client, Query=None, Msg=None, Data=None):
        self.client = Client
        self.query = Query
        self.msg = Msg
        self.data = Data

    async def retChat(self):
        return self.query.message if self.query else self.msg

    async def sendMsg(self, **kwargs):
        # 兼容 type/send 两种强制新消息标志
        # 包含视频判断、var 写入、RPCError 捕获
```

### 兼容性说明

- `sendMsg` 中 `force_send` 同时兼容原有的 `type` 和 `send` 两个 kwarg，调用方无需修改
- admin 的 `sendMsg` 没有 `var` 写入逻辑，基类统一加上（无副作用，因为只有传入 `var=True` 时才写）

### 受影响文件

| 文件 | 修改内容 |
|------|---------|
| `views/base.py` | 新建 |
| `views/client/task.py` | 5 个类继承 BaseView，删除重复方法 |
| `views/client/publish.py` | 5 个类继承 BaseView，删除重复方法 |
| `views/admin/index.py` | Admin 类继承 BaseView，删除重复方法 |
