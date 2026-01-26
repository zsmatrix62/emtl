# EMT - 东方财富自动交易接口

EMT 是一个 Python 库，提供东方财富交易平台的程序化接口，支持多用户隔离、会话持久化和自动缓存管理。

## 特性

- **多用户隔离** - 每个用户拥有独立的 session 和验证状态
- **会话持久化** - 自动缓存登录会话，避免频繁验证码
- **过期管理** - 支持 TTL 过期机制，自动刷新会话
- **类型安全** - 完整的类型注解，IDE 友好
- **简单易用** - 清晰的 API 设计，快速上手

## 安装

```bash
# 使用 pip
pip install emtl

# 或使用 uv（推荐）
uv pip install emtl
```

## 快速开始

### 基础用法

```python
from emtl import EMTClient

# 创建客户端并登录
client = EMTClient()
client.login("your_username", "your_password")

# 查询资产
asset = client.query_asset_and_position()
print(asset)

# 查询订单
orders = client.query_orders()
print(orders)
```

### 使用 ClientManager（推荐）

`ClientManager` 自动管理会话缓存，避免重复登录：

```python
from emtl import ClientManager, DillSerializer, LoginFailedError

manager = ClientManager(DillSerializer())

try:
    # 首次调用会登录并缓存
    client = manager.get_client("your_username", "your_password")

    # 后续调用直接从缓存加载，无需登录
    client = manager.get_client("your_username", "your_password")

    # 查询操作
    orders = client.query_orders()
    print(orders)
except LoginFailedError as e:
    print(f"登录失败: {e}")
```

## API 参考

### EMTClient

主要的客户端类，处理所有交易操作。

#### 构造函数

```python
client = EMTClient()
```

#### 方法

##### `login(username: str = "", password: str = "", duration: int = 30) -> Optional[str]`

登录到 EMT 平台。

**参数：**
- `username`: EMT 用户名（默认从 `EM_USERNAME` 环境变量读取）
- `password`: 密码明文（默认从 `EM_PASSWORD` 环境变量读取）
- `duration`: 会话持续时间（分钟），默认 30

**返回：**
- 成功返回验证 key 字符串
- 失败返回 `None`

**示例：**
```python
# 直接传参
client.login("username", "password")

# 使用环境变量
import os
os.environ["EM_USERNAME"] = "username"
os.environ["EM_PASSWORD"] = "password"
client.login()
```

##### `query_asset_and_position() -> Optional[dict]`

查询资产和持仓信息。

**返回：**
```python
{
    "Status": 0,
    "Data": [{
        "Kqzj": "可用资金",
        "Kyzj": "总资产",
        "positions": [...],  # 持仓列表
    }]
}
```

##### `query_orders() -> Optional[dict]`

查询当前委托订单。

**返回：**
```python
{
    "Status": 0,
    "Data": [{
        "Wtbh": "委托编号",
        "Wtrq": "委托日期",
        "stockCode": "股票代码",
        "price": "委托价格",
        "amount": "委托数量",
        ...
    }]
}
```

##### `query_trades() -> Optional[dict]`

查询成交记录。

##### `query_history_orders(size: int, start_time: str, end_time: str) -> Optional[dict]`

查询历史订单。

**参数：**
- `size`: 查询条目数
- `start_time`: 开始时间，格式 `%Y-%m-%d`
- `end_time`: 结束时间，格式 `%Y-%m-%d`

**示例：**
```python
client.query_history_orders(100, "2024-01-01", "2024-01-31")
```

##### `query_history_trades(size: int, start_time: str, end_time: str) -> Optional[dict]`

查询历史成交。

##### `query_funds_flow(size: int, start_time: str, end_time: str) -> Optional[dict]`

查询资金流水。

##### `create_order(stock_code: str, trade_type: str, market: str, price: float, amount: int) -> Optional[dict]`

创建交易订单。

**参数：**
- `stock_code`: 股票代码（如 "600000"）
- `trade_type`: 交易方向，`"B"` 买入，`"S"` 卖出
- `market`: 市场，`"HA"` 上海，`"SA"` 深圳
- `price`: 委托价格
- `amount`: 委托数量（股）

**示例：**
```python
# 买入 100 股浦发银行，价格 10.50
client.create_order("600000", "B", "HA", 10.50, 100)

# 卖出
client.create_order("000002", "S", "SA", 8.00, 200)
```

##### `cancel_order(order_str: str) -> str`

取消订单。

**参数：**
- `order_str`: 订单字符串，格式为 `{日期}_{编号}`，如 `"20240126_123456"`

**示例：**
```python
orders = client.query_orders()
order_str = f"{orders['Data'][0]['Wtrq']}_{orders['Data'][0]['Wtbh']}"
client.cancel_order(order_str)
```

##### `get_last_price(symbol_code: str, market: str) -> float`

获取最新股价。

**参数：**
- `symbol_code`: 股票代码
- `market`: 市场，`"HA"` 或 `"SA"`

**返回：**
- 最新价格，如果获取失败返回 `float("nan")`

### ClientManager

客户端管理器，自动处理会话缓存和过期。

#### 构造函数

```python
manager = ClientManager(serializer, default_ttl=1800)
```

**参数：**
- `serializer`: 序列化器实例（如 `DillSerializer()`）
- `default_ttl`: 默认缓存时间（秒），默认 1800（30 分钟）

#### 方法

##### `get_client(username: str, password: str, ttl: int | None = None) -> EMTClient`

获取客户端实例。

**行为：**
1. 尝试从缓存加载
2. 如果缓存存在且未过期，直接返回
3. 否则创建新客户端、登录、保存到缓存

**参数：**
- `username`: 用户名
- `password`: 密码
- `ttl`: 可选的缓存时间（秒），覆盖默认值

**抛出：**
- `LoginFailedError`: 登录失败时

##### `invalidate(username: str) -> bool`

使缓存失效。

##### `list_cached_users() -> list[str]`

列出所有已缓存且未过期的用户。

### DillSerializer

默认的序列化实现，使用 dill 库。

#### 构造函数

```python
serializer = DillSerializer(storage_dir=None)
```

**存储目录优先级：**
1. 环境变量 `EMTL_STORAGE_DIR`
2. 构造参数 `storage_dir`
3. 默认当前目录 `.emtl/`

**示例：**
```bash
# 设置环境变量
export EMTL_STORAGE_DIR=/path/to/storage
python your_app.py
```

```python
# 或在代码中指定
from emtl import DillSerializer

serializer = DillSerializer("/custom/path")
```

## 异常

EMT 使用异常层级来处理不同类型的错误：

### 异常层级

```
EmtlException
├── LoginFailedError     # 登录失败
├── EmAPIError           # API 请求错误
└── SerializerError      # 序列化错误
```

### EmtlException

所有 EMT 异常的基类。可以用于捕获所有 EMT 相关错误：

```python
from emtl import EmtlException

try:
    client.query_orders()
except EmtlException as e:
    print(f"EMT 错误: {e}")
```

### LoginFailedError

登录失败时抛出，可能原因：
- 用户名或密码错误
- 验证码识别失败
- 账户被锁定
- 网络问题

```python
from emtl import LoginFailedError

try:
    client = manager.get_client("user", "pass")
except LoginFailedError as e:
    print(f"登录失败: {e}")
    # Login failed for user 'user'. Please check username, password, and captcha.
```

### EmAPIError

API 请求失败时抛出，可能原因：
- HTTP 错误（非 200 状态码）
- API 返回错误状态（Status == -1）
- 网络连接问题

```python
from emtl import EmAPIError

try:
    orders = client.query_orders()
except EmAPIError as e:
    print(f"API 错误: {e}")
    print(f"状态码: {e.status_code}")
    print(f"响应: {e.response}")
```

### SerializerError

序列化操作失败时抛出。

```python
from emtl import SerializerError

try:
    manager = ClientManager(DillSerializer())
    client = manager.get_client("user", "pass")
except SerializerError as e:
    print(f"序列化错误: {e}")
```

## 最佳实践

### 1. 使用 ClientManager 管理会话

```python
from emtl import ClientManager, DillSerializer

# 全局共享的 manager
manager = ClientManager(DillSerializer())

def get_user_client(username: str, password: str):
    """获取用户客户端，自动处理缓存"""
    return manager.get_client(username, password)

# 使用
client = get_user_client("user1", "pass1")
orders = client.query_orders()
```

### 2. 错误处理

```python
from emtl import (
    ClientManager, DillSerializer,
    EmtlException, LoginFailedError, EmAPIError
)

manager = ClientManager(DillSerializer())

try:
    client = manager.get_client(username, password)
    # 执行交易操作
except LoginFailedError as e:
    print(f"登录失败: {e}")
except EmAPIError as e:
    print(f"API 错误: {e} (status_code={e.status_code})")
except EmtlException as e:
    print(f"EMT 错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

### 3. 多用户管理

```python
from emtl import ClientManager, DillSerializer

class TradingBot:
    def __init__(self):
        self.manager = ClientManager(DillSerializer())

    def trade_for_user(self, username: str, password: str, stock: str, price: float):
        """为指定用户执行交易"""
        client = self.manager.get_client(username, password)

        # 检查资产
        asset = client.query_asset_and_position()
        available = float(asset["Data"][0]["Kqzj"])

        if available >= price * 100:
            result = client.create_order(stock, "B", "HA", price, 100)
            print(f"下单成功: {result}")
        else:
            print("资金不足")

# 使用
bot = TradingBot()
bot.trade_for_user("user1", "pass1", "600000", 10.50)
```

### 4. 配置存储目录

```python
import os
from emtl import ClientManager, DillSerializer

# 方式1: 环境变量（推荐）
os.environ["EMTL_STORAGE_DIR"] = "./data/emtl_cache"
manager = ClientManager(DillSerializer())

# 方式2: 直接指定
manager = ClientManager(DillSerializer("./data/emtl_cache"))
```

### 5. 会话过期处理

```python
from emtl import ClientManager, DillSerializer

# 设置较短的 TTL 用于测试
manager = ClientManager(DillSerializer(), default_ttl=600)  # 10 分钟

# 首次调用会登录并缓存
client = manager.get_client("user", "pass")

# 10 分钟内再次调用，直接从缓存加载
client = manager.get_client("user", "pass")

# 10 分钟后调用，自动重新登录
client = manager.get_client("user", "pass")
```

## 环境变量

| 变量名 | 说明 |
|--------|------|
| `EM_USERNAME` | 默认用户名 |
| `EM_PASSWORD` | 默认密码 |
| `EMTL_STORAGE_DIR` | 缓存存储目录 |

## 注意事项

1. **验证码识别**: 登录依赖验证码识别，可能偶尔失败，`ClientManager` 会自动重试
2. **会话过期**: 默认 TTL 30 分钟，过期后自动重新登录
3. **线程安全**: 每个客户端实例不是线程安全的，多线程请为每个线程创建独立实例
4. **密码安全**: 建议使用环境变量存储密码，避免硬编码

## API 响应示例

运行 `python main.py` 会调用所有 API 方法并将响应保存到 `./examples/emapi/` 目录：

```bash
python main.py
```

生成的示例文件：

| 文件 | 说明 |
|------|------|
| `query_orders.json` | 查询当前委托订单 |
| `query_trades.json` | 查询成交记录 |
| `query_asset_and_position.json` | 查询资产和持仓 |
| `query_history_orders.json` | 查询历史订单（30天） |
| `query_history_trades.json` | 查询历史成交（30天） |
| `query_funds_flow.json` | 查询资金流水（30天） |
| `get_last_price.json` | 获取最新股价 |

这些示例文件展示了 API 的实际响应格式，可用于参考和测试。

## 开发

```bash
# 使用 uv
uv sync

# 迓行示例
python main.py
```

## License

MIT
