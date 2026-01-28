# EMT - 东方财富自动交易接口

EMT 是一个 Python 库，提供东方财富交易平台的程序化接口，支持多用户隔离、会话持久化和自动缓存管理。

> **注意**: 本项目是从 [riiy/emtl](https://github.com/riiy/emtl) fork 并进行重大改进的版本。

## 与原项目的主要区别

| 特性 | 原项目 (riiy/emtl) | 本项目 |
|------|-------------------|--------|
| **多用户支持** | ❌ 单用户（全局变量） | ✅ `EMTClient` 类，每用户独立状态 |
| **会话管理** | ❌ 无缓存机制 | ✅ `ClientManager` + 序列化，自动缓存 |
| **过期处理** | ❌ 无 | ✅ API 验证机制，自动重新登录 |
| **异常处理** | ⚠️ 基础异常 | ✅ 完整异常层级 (`EmtlException`, `LoginFailedError`, `EmAPIError`) |
| **类型安全** | ⚠️ 部分类型注解 | ✅ 完整类型注解 |
| **OCR 实例** | 每客户端独立 | ✅ 全局共享，节省资源 |
| **配置方式** | 硬编码 | ✅ 环境变量 + 多层次配置 |
| **API 封装** | 模块级函数 | ✅ 面向对象 + 向后兼容 |

## 架构改进

```
原项目:                    本项目:
┌─────────────┐           ┌─────────────────────────────┐
│  core.py    │           │    client.py (EMTClient)   │
│  全局变量    │           │    - session (隔离)         │
│  - session  │           │    - _em_validate_key (隔离)│
│  - ocr      │           │    - username (存储)        │
│  - key      │           │                             │
└─────────────┘           │    ocr (全局共享)           │
                           │                             │
                           │    client_manager.py         │
                           │    └── 自动缓存 + 过期管理     │
                           │                             │
                           │    serializer.py              │
                           │    └── 抽象序列化接口          │
                           │                             │
                           │    error.py                   │
                           │    └── 异常层级                 │
                           └─────────────────────────────┘
```

## 特性

- **多用户隔离** - 每个用户拥有独立的 session 和验证状态
- **会话持久化** - 自动缓存登录会话，避免频繁验证码
- **会话验证** - 通过 API 调用验证会话有效性，自动刷新过期会话
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

```python
from emtl import EMTClient

client = EMTClient()
client.login("username", "password")
```

**方法：**
- `login(username, password, duration=180)` - 登录
- `query_asset_and_position()` - 查询资产和持仓
- `query_orders()` - 查询当前委托订单
- `query_trades()` - 查询成交记录
- `query_history_orders(size, start_time, end_time)` - 查询历史订单
- `query_history_trades(size, start_time, end_time)` - 查询历史成交
- `query_funds_flow(size, start_time, end_time)` - 查询资金流水
- `create_order(stock_code, trade_type, market, price, amount)` - 创建订单
- `cancel_order(order_str)` - 取消订单
- `get_last_price(symbol_code, market)` - 获取最新股价

```python
# 买入示例
client.create_order("600000", "B", "HA", 10.50, 100)

# 查询历史
client.query_history_orders(100, "2024-01-01", "2024-01-31")
```

### ClientManager

```python
from emtl import ClientManager, DillSerializer

manager = ClientManager(DillSerializer())
client = manager.get_client("username", "password")
```

**方法：**
- `get_client(username, password, max_retries=3)` - 获取客户端（自动缓存+验证）
- `invalidate(username)` - 使缓存失效
- `list_cached_users()` - 列出已缓存用户

### DillSerializer

```python
from emtl import DillSerializer

# 默认存储目录：./emtl/
serializer = DillSerializer()

# 自定义目录
serializer = DillSerializer("/custom/path")
```

**存储目录优先级：** `EMTL_STORAGE_DIR` 环境变量 > 构造参数 > 默认 `./emtl/`

## 异常

```
EmtlException (基类)
├── LoginFailedError     # 登录失败
├── SessionExpiredError  # 会话过期
├── EmAPIError           # API 错误
└── SerializerError      # 序列化错误
```

```python
from emtl import EmtlException, LoginFailedError, EmAPIError

try:
    client = manager.get_client("user", "pass")
    orders = client.query_orders()
except LoginFailedError as e:
    print(f"登录失败: {e}")
except EmAPIError as e:
    print(f"API 错误: {e}")
except EmtlException as e:
    print(f"EMT 错误: {e}")
```

## 最佳实践

### 使用 ClientManager

```python
from emtl import ClientManager, DillSerializer

manager = ClientManager(DillSerializer())
client = manager.get_client("username", "password")
orders = client.query_orders()
```

### 配置存储目录

```python
import os
os.environ["EMTL_STORAGE_DIR"] = "./cache"
manager = ClientManager(DillSerializer())
```

### 完整配置

```python
import os
os.environ["EM_USERNAME"] = "your_username"
os.environ["EM_PASSWORD"] = "your_password"
os.environ["EMTL_STORAGE_DIR"] = "./data/cache"

from emtl import ClientManager, DillSerializer

manager = ClientManager(DillSerializer())
client = manager.get_client()
```

## 环境变量与配置

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `EM_USERNAME` | EMT 登录用户名 | 无 |
| `EM_PASSWORD` | EMT 登录密码 | 无 |
| `EMTL_STORAGE_DIR` | 缓存存储目录 | `./emtl/` |

### 存储目录配置

```python
import os
from emtl import ClientManager, DillSerializer

# 优先级: 环境变量 > 构造参数 > 默认
os.environ["EMTL_STORAGE_DIR"] = "./cache"
manager = ClientManager(DillSerializer())
```

### 默认值

| 配置 | 默认值 |
|------|--------|
| `EMTL_STORAGE_DIR` | `./emtl/` |
| `ClientManager.max_retries` | `3` 次重试 |
| `EMTClient.login(duration)` | `180` 分钟 (3 小时) |

## 注意事项

1. **验证码识别**: 登录依赖验证码识别，可能偶尔失败，`ClientManager` 会自动重试（最多 3 次）
2. **会话验证**: 每次从缓存加载客户端时会验证会话有效性，过期会话会自动重新登录
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

---

## 致谢

本项目是基于 [riiy/emtl](https://github.com/riiy/emtl) 的 fork 版本。

感谢原作者 [Riiy](https://github.com/riiy) 提供的原始实现和基础框架。

本项目在原有基础上进行了以下改进：
- 重构为面向对象架构，支持多用户隔离
- 添加会话持久化和自动缓存机制
- 完善异常处理和错误报告
- 提供完整的类型注解和文档

原项目仓库: [https://github.com/riiy/emtl](https://github.com/riiy/emtl)
