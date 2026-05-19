"""
xd.jydao.cn 支付通道下单 demo（占位版，待对文档后调整）。

用法:
    python pay_demo.py --amount 1.00 --bank 901

注意:
    - 商户密钥强烈建议改为从环境变量读取，不要硬编码到仓库里。
    - 接口路径、字段名、签名规则需按官方文档核对，本文件按国内常见"四方"通道
      模板编写：MD5 大写签名 + form-urlencoded POST。
"""

from __future__ import annotations

import argparse
import hashlib
import os
import time
import uuid
from datetime import datetime
from urllib.parse import urlencode

import requests


GATEWAY_BASE = "https://xd.jydao.cn"
ORDER_PATH = "/Pay_Index.html"  # TODO: 以文档为准

MERCHANT_ID = os.environ.get("JYDAO_MERCHANT_ID", "1021")
MERCHANT_KEY = os.environ.get("JYDAO_MERCHANT_KEY", "")  # 不要硬编码到代码里

NOTIFY_URL = os.environ.get("JYDAO_NOTIFY_URL", "https://your.domain/notify")
RETURN_URL = os.environ.get("JYDAO_RETURN_URL", "https://your.domain/return")


def make_sign(params: dict, key: str) -> str:
    """
    通用签名: 过滤空值 -> 按 key 字典序排序 -> key=value&... -> 末尾 &key=商户密钥 -> MD5 大写
    """
    filtered = {k: v for k, v in params.items() if v not in (None, "") and k != "pay_md5sign"}
    items = sorted(filtered.items(), key=lambda kv: kv[0])
    raw = "&".join(f"{k}={v}" for k, v in items) + f"&key={key}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()


def build_order(amount: str, bank_code: str) -> dict:
    return {
        "pay_memberid": MERCHANT_ID,
        "pay_orderid": f"T{int(time.time())}{uuid.uuid4().hex[:6]}",
        "pay_applydate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pay_bankcode": bank_code,           # e.g. 901=支付宝 902=微信，按文档
        "pay_notifyurl": NOTIFY_URL,
        "pay_callbackurl": RETURN_URL,
        "pay_amount": amount,                # 字符串，2 位小数
        "pay_productname": "test-order",
    }


def create_order(amount: str, bank_code: str) -> None:
    if not MERCHANT_KEY:
        raise SystemExit("请先设置环境变量 JYDAO_MERCHANT_KEY")

    params = build_order(amount, bank_code)
    params["pay_md5sign"] = make_sign(params, MERCHANT_KEY)

    url = GATEWAY_BASE + ORDER_PATH
    print(f"POST {url}")
    print("payload:")
    for k, v in params.items():
        print(f"  {k} = {v}")

    resp = requests.post(
        url,
        data=params,
        headers={"User-Agent": "pay-demo/0.1"},
        timeout=15,
        allow_redirects=False,
    )

    print(f"\nstatus = {resp.status_code}")
    print(f"location = {resp.headers.get('Location')}")
    print(f"content-type = {resp.headers.get('Content-Type')}")
    print("body (first 2KB):")
    print(resp.text[:2048])


def verify_notify(form: dict, key: str) -> bool:
    """异步回调验签：剔除 sign 字段后用同样规则重算"""
    received = form.get("sign") or form.get("pay_md5sign") or ""
    expected = make_sign({k: v for k, v in form.items() if k not in ("sign", "pay_md5sign")}, key)
    return received.upper() == expected


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--amount", default="1.00", help="支付金额（元，2 位小数）")
    ap.add_argument("--bank", default="901", help="支付方式编码，文档为准")
    args = ap.parse_args()
    create_order(args.amount, args.bank)
