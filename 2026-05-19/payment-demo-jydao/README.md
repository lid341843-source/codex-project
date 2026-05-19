# jydao 支付通道 demo

> 字段名 / 接口路径 / 签名规则按国内"四方"通道最常见模板写（`pay_memberid` 系列 + MD5 大写）。
> 文档里如有差异，以文档为准。

## 两种使用方式

### A. 浏览器一键测试（最省事）

```bash
export JYDAO_MERCHANT_KEY=<你的商户密钥>     # 建议先在通道后台重置一次
export JYDAO_NOTIFY_URL=https://your.domain/notify
export JYDAO_RETURN_URL=https://your.domain/return

python3 pay_demo.py form --amount 1.00 --bank 901 --out pay.html
# 然后浏览器双击打开 pay.html → 自动 POST 到网关 → 出现支付页就是签名通过
```

### B. 部署成 HTTP 服务

```bash
JYDAO_MERCHANT_KEY=xxx \
JYDAO_NOTIFY_URL=https://your.domain/notify \
JYDAO_RETURN_URL=https://your.domain/return \
python3 pay_demo.py serve --host 0.0.0.0 --port 8080

# 然后浏览器访问
#   http://<server>:8080/pay?amount=1.00&bank=901
```

只用了 Python 标准库（`http.server` + `hashlib`），不需要 `pip install`。

## 文档需要核对的字段

| 位置 | 当前占位 | 文档需对照 |
| --- | --- | --- |
| `ORDER_PATH` | `/Pay_Index.html` | 实际下单接口路径 |
| 字段名 | `pay_memberid` / `pay_orderid` / `pay_applydate` / `pay_bankcode` / `pay_notifyurl` / `pay_callbackurl` / `pay_amount` / `pay_md5sign` | 是否一致；是否还有必填项 |
| `pay_bankcode` | 901 / 902 | 文档支付方式编码表 |
| 签名 | 字典序拼接 + `&key=商户密钥` + MD5 大写 | 是否一致 |

## 调试

打开 `pay.html` 后如果跳转的不是支付页而是错误页（如"签名错误"/"参数缺失"），把：

1. 错误码 / 错误文案
2. `pay_demo.py form` 打印出来的所有 signed params

发回来，我对一下文档把 `ORDER_PATH` 或字段名改对。

## 安全

- 商户密钥从环境变量读取，不进仓库。
- 由于密钥曾在沟通里出现，建议先在通道后台重置一次。
