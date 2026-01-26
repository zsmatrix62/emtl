# EMTClient 使用说明

## 概述

`EMTClient` 是东方财富自动交易接口的客户端适配器，支持多用户隔离使用。每个客户端实例拥有独立的 session、OCR 实例和验证 key。

## 安装

```bash
# 使用 pip 安装
pip install emtl

# 或使用 uv（推荐）
uv pip install emtl
```

## 单用户使用（向后兼容）

```python
import emtl

# 登录
emtl.login("你的用户名", "你的密码")

# 查询订单
orders = emtl.query_orders()
print(orders)

# 查询资产和持仓
asset = emtl.query_asset_and_position()
print(asset)

# 创建订单
emtl.create_order(
    stock_code="600000",
    trade_type="B",  # B=买入, S=卖出
    market="HA",      # HA=上海, SA=深圳
    price=10.50,
    amount=100
)

# 取消订单
emtl.cancel_order("20240126_123456")
```

## 多用户使用

### 基本用法

```python
from emtl import EMTClient

# 创建用户1的客户端
user1 = EMTClient()
user1.login("用户1的用户名", "用户1的密码")

# 创建用户2的客户端
user2 = EMTClient()
user2.login("用户2的用户名", "用户2的密码")

# 每个用户独立操作
user1_orders = user1.query_orders()
user2_orders = user2.query_orders()

print(f"用户1的订单: {user1_orders}")
print(f"用户2的订单: {user2_orders}")
```

### 使用环境变量

```python
import os
from emtl import EMTClient

# 设置环境变量
os.environ['EM_USERNAME'] = '540975189038'
os.environ['EM_PASSWORD'] = '123731'

# 登录时自动从环境变量读取
client = EMTClient()
client.login()  # 不传参数，自动使用环境变量
```

## API 方法

### EMTClient

| 方法 | 说明 |
|------|------|
| `login(username, password, duration=30)` | 登录，duration 为在线时长（分钟） |
| `query_asset_and_position()` | 查询资产和持仓 |
| `query_orders()` | 查询当前订单 |
| `query_trades()` | 查询成交记录 |
| `query_history_orders(size, start_time, end_time)` | 查询历史订单 |
| `query_history_trades(size, start_time, end_time)` | 查询历史成交 |
| `query_funds_flow(size, start_time, end_time)` | 查询资金流水 |
| `create_order(stock_code, trade_type, market, price, amount)` | 创建订单 |
| `cancel_order(order_str)` | 取消订单 |
| `get_last_price(symbol_code, market)` | 获取最新价格 |

## 隔离性说明

每个 `EMTClient` 实例拥有完全独立的状态：

- `session`: 独立的 HTTP 会话，互不干扰
- `ocr`: 独立的验证码识别实例
- `_em_validate_key`: 独立的登录验证 key

## 开发环境设置

```bash
# 使用 uv
uv sync

# 运行测试
uv run pytest
```

## 注意事项

1. **验证码识别**: 登录时需要识别验证码，可能存在识别失败的情况，建议增加重试机制
2. **session 过期**: 如果 session 过期，需要重新调用 `login()` 方法
3. **多线程**: 每个客户端实例不是线程安全的，多线程环境下应为每个线程创建独立的客户端实例

## License

MIT
