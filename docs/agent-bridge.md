# Agent Bridge

> Nusantara Retail Twin 与多智能体决策引擎的桥接协议。
> 版本：v0.1 · 协议：Agent-Fleet-Spec v0.1

---

## 1. 设计目标

**物理世界与决策世界的解耦**。Nusantara Retail Twin 负责空间、库存、预测的**状态表达**；多智能体引擎负责**决策推理**。两者通过标准化事件流通信，任一侧可独立升级。

**降级可用**。当 Agent 引擎不可达时，系统自动切换为内置模拟器，前端状态灯区分「实时联动」与「演示模拟」，不阻塞任何业务操作。

**协议可审计**。所有事件以 `STATE_EVENT` 信封传输，携带完整元数据（时间戳、智能体身份、追踪 ID），可回放、可审计。

**区域感知**。智能体身份 URI 包含信任域，支持印尼、澳洲等多区域部署。

---

## 2. 智能体拓扑

Nusantara Retail Twin 生态包含五类核心智能体：

```text
┌───────────────────────────────────────────────────────┐
│                Agent Fleet (ID)                        │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Forecast    │  │ Replenish    │  │  Pricing     │ │
│  │  Agent       │  │  Dispatch    │  │  Agent       │ │
│  │              │  │  Agent       │  │              │ │
│  │  需求预测     │  │  补货调度     │  │  动态定价     │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                 │         │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐ │
│  │  Promotion   │  │  Lifecycle   │  │  Sentiment   │ │
│  │  Trigger     │  │  Manager     │  │  Watcher     │ │
│  │              │  │              │  │              │ │
│  │  促销触发     │  │  生命周期     │  │  舆情监控     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
└───────────────────────────────────────────────────────┘
                          │
                          │ STATE_EVENT stream
                          ▼
┌───────────────────────────────────────────────────────┐
│           Nusantara Retail Twin Core                   │
│  Spatial · Inventory · Forecast · Replenishment        │
└───────────────────────────────────────────────────────┘
```

---

## 3. 智能体身份

每个智能体拥有唯一 URI：

```text
agent://{trust-domain}/{fleet}/{role}/{instance}
```

**示例**：

```text
agent://nusantara.id/retail-core/forecast/m-01
agent://nusantara.id/retail-core/replenish/m-01
agent://nusantara.id/retail-core/pricing/m-01
agent://nusantara.id/retail-core/promotion/m-01
agent://nusantara.id/retail-core/lifecycle/m-01
agent://nusantara.id/retail-core/sentiment/m-01
```

| 字段 | 说明 | 示例 |
|---|---|---|
| `trust-domain` | 信任域（区域部署） | `nusantara.id`、`aegis.au` |
| `fleet` | 集群名 | `retail-core` |
| `role` | 智能体角色 | `forecast`、`replenish` |
| `instance` | 实例 ID | `m-01`、`w-02` |

---

## 4. 消息信封

所有事件使用统一 `STATE_EVENT` 信封：

```json
{
  "spec_version": "afs/v0.1",
  "event_type": "STATE_EVENT",
  "event_id": "evt-uuid",
  "trace_id": "trace-uuid",
  "timestamp": "2026-10-14T08:30:00.000+07:00",
  "source": "agent://nusantara.id/retail-core/forecast/m-01",
  "target": "agent://nusantara.id/retail-core/twin/m-01",
  "domain": "nusantara.id",
  "payload": {
    "kind": "forecast.update",
    "store_id": "st-2000-java-001",
    "sku_id": "sku-001",
    "data": {
      "demand_mean": 14.2,
      "demand_p90": 22.0,
      "horizon_days": 30,
      "confidence": 0.87
    }
  },
  "meta": {
    "priority": "normal",
    "ttl_seconds": 300,
    "requires_ack": false
  }
}
```

**字段说明**：

| 字段 | 必填 | 说明 |
|---|---|---|
| `spec_version` | ✓ | 协议版本，固定 `afs/v0.1` |
| `event_type` | ✓ | `STATE_EVENT` / `COMMAND` / `ACK` / `ERROR` |
| `event_id` | ✓ | 事件唯一 ID |
| `trace_id` | ✓ | 全链路追踪 ID |
| `timestamp` | ✓ | ISO 8601 带时区 |
| `source` | ✓ | 发送方 URI |
| `target` | | 目标 URI，广播时省略 |
| `domain` | ✓ | 信任域 |
| `payload` | ✓ | 事件载荷 |
| `meta` | | 元数据 |

---

## 5. 事件类型

### 5.1 状态事件（STATE_EVENT）

| kind | 方向 | 说明 |
|---|---|---|
| `forecast.update` | Forecast → Twin | 预测结果更新 |
| `replenish.order` | Replenish → Twin | 补货建议生成 |
| `pricing.adjust` | Pricing → Twin | 价格调整建议 |
| `promotion.trigger` | Promotion → Twin | 促销触发 |
| `lifecycle.action` | Lifecycle → Twin | 生命周期动作（FEFO / 降价） |
| `sentiment.signal` | Sentiment → Twin | 舆情信号更新 |
| `twin.state` | Twin → All | 空间/库存状态广播 |

### 5.2 命令事件（COMMAND）

| kind | 方向 | 说明 |
|---|---|---|
| `twin.run_simulation` | Agent → Twin | 请求运行补货模拟 |
| `twin.load_store` | Agent → Twin | 请求加载门店 |
| `twin.optimize_planogram` | Agent → Twin | 请求运行空间优化 |

### 5.3 确认事件（ACK）

```json
{
  "spec_version": "afs/v0.1",
  "event_type": "ACK",
  "event_id": "evt-uuid",
  "trace_id": "trace-uuid",
  "timestamp": "2026-10-14T08:30:01.000+07:00",
  "source": "agent://nusantara.id/retail-core/twin/m-01",
  "payload": {
    "ack_event_id": "evt-uuid",
    "status": "received",
    "processed_at": "2026-10-14T08:30:01.000+07:00"
  }
}
```

### 5.4 错误事件（ERROR）

```json
{
  "spec_version": "afs/v0.1",
  "event_type": "ERROR",
  "event_id": "evt-uuid",
  "trace_id": "trace-uuid",
  "timestamp": "2026-10-14T08:30:01.000+07:00",
  "source": "agent://nusantara.id/retail-core/twin/m-01",
  "payload": {
    "error_code": "AGENT_UNREACHABLE",
    "message": "Forecast agent did not respond within TTL",
    "original_event_id": "evt-uuid",
    "retry_after_seconds": 30
  }
}
```

---

## 6. 传输层

### 6.1 WebSocket（主通道）

```text
ws://localhost:4000/ws/agents
```

**订阅**：

```json
{
  "action": "subscribe",
  "domains": ["nusantara.id"],
  "kinds": ["forecast.update", "replenish.order", "promotion.trigger"],
  "store_id": "st-2000-java-001"
}
```

**服务端确认**：

```json
{
  "action": "subscribed",
  "subscription_id": "sub-uuid",
  "kinds": ["forecast.update", "replenish.order", "promotion.trigger"]
}
```

**心跳**：

```json
{ "action": "ping", "timestamp": "ISO8601" }
{ "action": "pong", "timestamp": "ISO8601" }
```

### 6.2 REST（查询与回放）

| 端点 | 方法 | 说明 |
|---|---|---|
| `/api/agents/events` | GET | 查询历史事件 |
| `/api/agents/afs/events` | GET | 获取原始 AFS 信封 |
| `/api/agents/status` | GET | 智能体状态 |
| `/api/agents/command` | POST | 发送命令事件 |

**查询历史事件**：

```text
GET /api/agents/events?store_id=st-2000-java-001&kind=forecast.update&since=2026-10-14T00:00:00&limit=100
```

**响应**：

```json
{
  "events": [
    {
      "event_id": "evt-uuid",
      "kind": "forecast.update",
      "timestamp": "ISO8601",
      "source": "agent://nusantara.id/retail-core/forecast/m-01",
      "payload": { }
    }
  ],
  "total": 42,
  "has_more": false
}
```

### 6.3 模式切换

配置 `integration/energy-agent-config.json`：

```json
{
  "mode": "local",
  "omniAgentX": {
    "baseUrl": "http://localhost:5000",
    "apiKey": "",
    "timeout_seconds": 10
  },
  "fallback": {
    "enabled": true,
    "simulator": "builtin"
  },
  "protocol": {
    "spec_version": "afs/v0.1",
    "accept_legacy_flat": true
  }
}
```

| mode | 说明 |
|---|---|
| `local` | 使用内置模拟器，不连接外部 Agent |
| `remote` | 连接真实 Agent 引擎 |
| `hybrid` | 优先 remote，失败时降级 local |

**状态灯区分**：

| 状态 | 前端显示 |
|---|---|
| `remote` 连通 | 🟢 OmniAgentX Live |
| `hybrid` 降级 | 🟡 Demo Simulation |
| `local` | ⚪ Offline Mode |

---

## 7. 智能体定义

### 7.1 Forecast Agent

**职责**：基于历史销售、节庆日历、舆情信号生成需求预测。

**输入**：

```json
{
  "kind": "forecast.request",
  "store_id": "st-2000-java-001",
  "sku_ids": ["sku-001", "sku-002"],
  "horizon_days": 30,
  "include_ramadan": true
}
```

**输出**：

```json
{
  "kind": "forecast.update",
  "store_id": "st-2000-java-001",
  "sku_id": "sku-001",
  "data": {
    "daily_forecast": [
      { "date": "2026-10-14", "demand_mean": 14.2, "demand_p90": 22.0 }
    ],
    "safety_stock": 18,
    "reorder_point": 42,
    "confidence": 0.87,
    "model_version": "prophet-lgbm-v0.1"
  }
}
```

### 7.2 Replenish Dispatch Agent

**职责**：基于预测、当前库存、有效提前期生成补货建议。

**输入**：

```json
{
  "kind": "replenish.request",
  "store_id": "st-2000-java-001",
  "strategy": "auto",
  "simulation_date": "2026-10-14"
}
```

**输出**：

```json
{
  "kind": "replenish.order",
  "store_id": "st-2000-java-001",
  "orders": [
    {
      "facing_id": "fc-2000-001-3-01",
      "sku_code": "SKU-001",
      "action": "ORDER",
      "order_quantity": 60,
      "priority": "HIGH",
      "reason": "stock_below_reorder_point",
      "suggested_delivery_window": "2026-10-15 to 2026-10-18"
    }
  ],
  "summary": {
    "total_orders": 18,
    "total_units": 840,
    "estimated_cost_idr": 12500000
  }
}
```

### 7.3 Pricing Agent

**职责**：根据去化速度、剩余保质期、竞争价格动态调价。

**输出**：

```json
{
  "kind": "pricing.adjust",
  "store_id": "st-2000-java-001",
  "sku_id": "sku-008",
  "data": {
    "current_price": 42000,
    "suggested_price": 37800,
    "discount_pct": 10,
    "reason": "expiring_in_2_days",
    "valid_until": "2026-10-16"
  }
}
```

### 7.4 Promotion Trigger Agent

**职责**：临期促销、斋月礼品装阶梯折扣、Mudik 套装触发。

**输出**：

```json
{
  "kind": "promotion.trigger",
  "store_id": "st-2000-java-001",
  "promotion_type": "bundle",
  "target_skus": ["sku-008", "sku-011"],
  "bundle_name": "Ayam + Bayam Combo",
  "discount_pct": 15,
  "valid_window": {
    "start": "2026-10-14",
    "end": "2026-10-16"
  },
  "reason": "fresh_expiring_bundle"
}
```

### 7.5 Lifecycle Manager Agent

**职责**：FEFO 批次分配、临期动作触发、清真认证链路。

**输出**：

```json
{
  "kind": "lifecycle.action",
  "store_id": "st-2000-java-001",
  "actions": [
    {
      "batch_id": "batch-uuid",
      "sku_id": "sku-008",
      "action": "BUNDLE_PROMOTION",
      "reason": "expires_in_2_days",
      "suggested_discount_pct": 15,
      "bundle_with_category": "vegetables"
    }
  ]
}
```

### 7.6 Sentiment Watcher Agent

**职责**：聚合社交媒体热点与情感趋势，输出品类级热度指数。

**输出**：

```json
{
  "kind": "sentiment.signal",
  "store_id": "st-2000-java-001",
  "signals": [
    {
      "category_id": "fashion",
      "heat_index": 0.72,
      "sentiment_score": 0.45,
      "source": "tiktok",
      "date": "2026-10-14"
    }
  ]
}
```

---

## 8. 典型流程

### 8.1 斋月前置补货

```text
[日历服务]
    │  2026-01-01 触发斋月前置窗口
    ▼
[Forecast Agent]
    │  生成斋月窗口需求曲线
    ▼
[Replenish Dispatch Agent]
    │  计算首轮补货量
    ▼
[Promotion Trigger Agent]
    │  生成礼品装阶梯折扣
    ▼
[Nusantara Retail Twin]
    │  更新 Planogram + 库存约束
    ▼
[3D 视图]
       节庆品类高亮 + 补货动画
```

### 8.2 临期生鲜触发

```text
[Lifecycle Manager Agent]
    │  检测到批次剩余保质期 ≤ 2 天
    ▼
[Promotion Trigger Agent]
    │  生成捆绑促销（肉类 + 蔬菜）
    ▼
[Pricing Agent]
    │  计算建议折扣 15%
    ▼
[Nusantara Retail Twin]
    │  更新促销标签 + 3D 高亮
    ▼
[前端]
       Facing 变橙色 + 促销气泡
```

### 8.3 舆情驱动预测

```text
[Sentiment Watcher Agent]
    │  检测到「Gamis Ramadhan」热度飙升
    ▼
[Forecast Agent]
    │  将热度作为外生变量注入预测
    ▼
[Nusantara Retail Twin]
    │  更新服饰区需求预测
    ▼
[Replenish Dispatch Agent]
    │  提前补货 Gamis / Koko
    ▼
[3D 视图]
       服饰区展示面位扩展
```

---

## 9. 降级策略

| 场景 | 行为 |
|---|---|
| Agent WebSocket 断连 | 自动重连（指数退避，最大 30s） |
| Agent 请求超时 | 降级到内置模拟器，状态灯变黄 |
| Agent 返回错误 | 记录 ERROR 事件，保留上次状态 |
| 协议版本不匹配 | 拒绝事件，返回 ERROR，提示升级 |
| 信任域不匹配 | 拒绝事件，记录安全日志 |

**内置模拟器**：

```python
class BuiltinSimulator:
    """当 Agent 不可达时，提供基于规则的模拟决策。"""
    
    def forecast(self, store_id, sku_id, horizon_days):
        # 基于历史均值 + 斋月乘数
        ...
    
    def replenish(self, store_id, sku_id):
        # 基于再订货点
        ...
    
    def pricing(self, store_id, sku_id):
        # 基于剩余保质期
        ...
```

---

## 10. 安全与信任

### 10.1 信任域

每个事件携带 `domain` 字段。接收方校验：

```python
def validate_domain(event, allowed_domains):
    if event["domain"] not in allowed_domains:
        raise SecurityError(f"Domain {event['domain']} not allowed")
```

**允许的信任域**：

```yaml
allowed_domains:
  - nusantara.id
  - partner.nusantara.id
```

### 10.2 认证

- WebSocket：连接时携带 `Authorization: Bearer <token>`
- REST：请求头 `X-API-Key`
- Agent 间：mTLS（生产环境）

### 10.3 速率限制

| 事件类型 | 限制 |
|---|---|
| `forecast.update` | 100 / 分钟 / store |
| `replenish.order` | 60 / 分钟 / store |
| `promotion.trigger` | 30 / 分钟 / store |
| `sentiment.signal` | 200 / 分钟 / store |

---

## 11. 配置示例

`integration/agent-bridge-config.json`：

```json
{
  "version": "0.1",
  "mode": "hybrid",
  "protocol": {
    "spec_version": "afs/v0.1",
    "accept_legacy_flat": true,
    "require_trace_id": true
  },
  "transport": {
    "websocket": {
      "url": "ws://localhost:4000/ws/agents",
      "reconnect_max_seconds": 30,
      "heartbeat_seconds": 15
    },
    "rest": {
      "base_url": "http://localhost:4000/api/agents",
      "timeout_seconds": 10
    }
  },
  "agents": {
    "forecast": {
      "uri": "agent://nusantara.id/retail-core/forecast/m-01",
      "enabled": true
    },
    "replenish": {
      "uri": "agent://nusantara.id/retail-core/replenish/m-01",
      "enabled": true
    },
    "pricing": {
      "uri": "agent://nusantara.id/retail-core/pricing/m-01",
      "enabled": true
    },
    "promotion": {
      "uri": "agent://nusantara.id/retail-core/promotion/m-01",
      "enabled": true
    },
    "lifecycle": {
      "uri": "agent://nusantara.id/retail-core/lifecycle/m-01",
      "enabled": true
    },
    "sentiment": {
      "uri": "agent://nusantara.id/retail-core/sentiment/m-01",
      "enabled": false
    }
  },
  "fallback": {
    "enabled": true,
    "simulator": "builtin",
    "notify_ui": true
  },
  "security": {
    "allowed_domains": ["nusantara.id"],
    "require_api_key": false,
    "rate_limit_enabled": true
  },
  "logging": {
    "level": "info",
    "retain_days": 30,
    "store_raw_envelopes": true
  }
}
```

---

## 12. 前端集成

### 12.1 状态灯

```tsx
function LiveStatusPill() {
  const { mode, connected } = useAgentFeed();
  
  const status = connected
    ? { label: 'OmniAgentX Live', color: 'green' }
    : mode === 'hybrid'
    ? { label: 'Demo Simulation', color: 'yellow' }
    : { label: 'Offline Mode', color: 'gray' };
  
  return <Pill label={status.label} color={status.color} />;
}
```

### 12.2 事件消费

```tsx
function useAgentFeed() {
  const [lastEvent, setLastEvent] = useState<AgentEvent | null>(null);
  
  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    ws.onopen = () => ws.send(JSON.stringify({
      action: 'subscribe',
      domains: ['nusantara.id'],
      kinds: ['forecast.update', 'replenish.order', 'promotion.trigger'],
    }));
    ws.onmessage = (msg) => {
      const event = JSON.parse(msg.data);
      if (event.event_type === 'STATE_EVENT') {
        setLastEvent(event);
      }
    };
    return () => ws.close();
  }, []);
  
  return { lastEvent };
}
```

---

## 13. 测试

### 13.1 单元测试

```python
def test_envelope_validation():
    event = build_state_event(
        source="agent://nusantara.id/retail-core/forecast/m-01",
        payload={"kind": "forecast.update", "data": {}},
    )
    assert validate_envelope(event) is True

def test_domain_security():
    event = build_state_event(domain="evil.com")
    with pytest.raises(SecurityError):
        validate_domain(event, allowed_domains=["nusantara.id"])
```

### 13.2 集成测试

```python
async def test_forecast_to_replenish_flow():
    # 1. 发送 forecast.update
    await bridge.publish(build_forecast_update())
    # 2. 等待 replenish.order
    event = await bridge.wait_for("replenish.order", timeout=5)
    assert event["payload"]["orders"][0]["action"] == "ORDER"
```

### 13.3 降级测试

```python
async def test_fallback_to_simulator():
    bridge = AgentBridge(mode="remote")
    await bridge.disconnect()  # 模拟 Agent 不可达
    result = await bridge.request_forecast(store_id, sku_id)
    assert bridge.mode == "hybrid"
    assert result["source"] == "builtin_simulator"
```

---

## 14. 更新日志

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-10 | v0.1 | 初始版本，覆盖智能体拓扑、协议信封、事件类型、传输层、降级策略 |
