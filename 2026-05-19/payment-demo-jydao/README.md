# jydao 支付通道 demo（占位版）

接口路径、字段、签名规则需按 https://xd.jydao.cn/doc/index.html 核对，下面的字段名是国内"四方"通道最常见的一套模板。

## 运行

```bash
export JYDAO_MERCHANT_ID=1021
export JYDAO_MERCHANT_KEY=<你的商户密钥>        # 强烈建议先重置一次
export JYDAO_NOTIFY_URL=https://your.domain/notify
export JYDAO_RETURN_URL=https://your.domain/return

pip install requests
python pay_demo.py --amount 1.00 --bank 901
```

## 需要按文档确认的位置（pay_demo.py 中的 TODO）

| 位置 | 当前占位 | 需要确认 |
| --- | --- | --- |
| `ORDER_PATH` | `/Pay_Index.html` | 文档里下单接口的真实路径 |
| 参数字段名 | `pay_memberid` / `pay_orderid` / `pay_applydate` / `pay_bankcode` / `pay_notifyurl` / `pay_callbackurl` / `pay_amount` / `pay_md5sign` | 是否一致；是否还有必填项（如 `pay_productname` / `attach` / `currency`） |
| `pay_bankcode` 编码 | `901` | 文档支付方式编码表 |
| 签名规则 | 字典序拼接 + `&key=商户密钥` + MD5 大写 | 是否一致（有的通道不带 `&key=`，有的用 HMAC-MD5） |
| 响应格式 | 表单 302 / HTML 自动提交 / JSON 含 `payurl` | 据此调整调用方处理逻辑 |
| 回调验签 | 同下单签名规则 | 文档回调字段表 |

## 调试小贴士

- 拿到第一次接口返回的错误码（如"签名错误"），优先用文档示例值复算签名串，对比明文 `raw` 看哪个字段差异。
- 如果文档里给了"签名示例"（参数+key 的拼接示例），把那段贴给我，我帮你对一下。

## 安全提醒

- 商户密钥不要进仓库；当前 `pay_demo.py` 已改成从环境变量读取。
- 由于密钥曾在对话/沟通里明文出现，建议在通道后台先重置一次。
