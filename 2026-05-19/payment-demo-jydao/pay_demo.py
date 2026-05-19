"""
xd.jydao.cn 支付通道下单 demo。

两种用法：

1) 生成自动提交表单（推荐先试这个，最稳）：
       python pay_demo.py form --amount 1.00 --bank 901 --out pay.html
   然后浏览器打开 pay.html，会自动 POST 到网关，看到支付页就说明签名通过。

2) 启动本地 HTTP 服务（用于部署到能联网的机器）：
       python pay_demo.py serve --host 0.0.0.0 --port 8080
   然后浏览器访问  http://<host>:8080/pay?amount=1.00&bank=901

注意:
    - 商户密钥从环境变量 JYDAO_MERCHANT_KEY 读取，不要硬编码。
    - 接口路径 / 字段名 / 签名规则按国内"四方"通道常见模板写，若文档不一致以文档为准。
"""

from __future__ import annotations

import argparse
import hashlib
import html
import os
import sys
import time
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse


GATEWAY_BASE = "https://xd.jydao.cn"
ORDER_PATH = "/Pay_Index.html"   # TODO: 以文档为准

MERCHANT_ID = os.environ.get("JYDAO_MERCHANT_ID", "1021")
MERCHANT_KEY = os.environ.get("JYDAO_MERCHANT_KEY", "")
NOTIFY_URL = os.environ.get("JYDAO_NOTIFY_URL", "https://example.com/notify")
RETURN_URL = os.environ.get("JYDAO_RETURN_URL", "https://example.com/return")


def make_sign(params: dict, key: str) -> str:
    filtered = {k: v for k, v in params.items() if v not in (None, "") and k != "pay_md5sign"}
    items = sorted(filtered.items(), key=lambda kv: kv[0])
    raw = "&".join(f"{k}={v}" for k, v in items) + f"&key={key}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()


def build_order(amount: str, bank_code: str) -> dict:
    return {
        "pay_memberid": MERCHANT_ID,
        "pay_orderid": f"T{int(time.time())}{uuid.uuid4().hex[:6]}",
        "pay_applydate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pay_bankcode": bank_code,
        "pay_notifyurl": NOTIFY_URL,
        "pay_callbackurl": RETURN_URL,
        "pay_amount": amount,
        "pay_productname": "test-order",
    }


def sign_order(amount: str, bank_code: str) -> dict:
    if not MERCHANT_KEY:
        raise SystemExit("请先设置环境变量 JYDAO_MERCHANT_KEY")
    params = build_order(amount, bank_code)
    params["pay_md5sign"] = make_sign(params, MERCHANT_KEY)
    return params


def render_form_html(params: dict) -> str:
    action = GATEWAY_BASE + ORDER_PATH
    hidden = "\n".join(
        f'    <input type="hidden" name="{html.escape(k)}" value="{html.escape(str(v))}">'
        for k, v in params.items()
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8">
<title>jydao pay redirect</title>
</head><body>
<p>正在跳转支付网关 {html.escape(action)} ...</p>
<form id="f" method="post" action="{html.escape(action)}">
{hidden}
  <noscript><button type="submit">手动提交</button></noscript>
</form>
<script>document.getElementById('f').submit();</script>
</body></html>
"""


def verify_notify(form: dict, key: str) -> bool:
    received = form.get("sign") or form.get("pay_md5sign") or ""
    expected = make_sign({k: v for k, v in form.items() if k not in ("sign", "pay_md5sign")}, key)
    return received.upper() == expected


# ---------- form 模式 ----------
def cmd_form(args: argparse.Namespace) -> None:
    params = sign_order(args.amount, args.bank)
    html_text = render_form_html(params)
    out = args.out or "pay.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_text)
    print(f"wrote {out}")
    print("--- signed params ---")
    for k, v in params.items():
        print(f"  {k} = {v}")
    print("\n打开这个文件浏览器会自动 POST 到网关：")
    print(f"  file://{os.path.abspath(out)}")


# ---------- serve 模式 ----------
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        u = urlparse(self.path)
        if u.path != "/pay":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not found")
            return
        q = parse_qs(u.query)
        amount = (q.get("amount") or ["1.00"])[0]
        bank = (q.get("bank") or ["901"])[0]
        try:
            params = sign_order(amount, bank)
        except SystemExit as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))
            return
        body = render_form_html(params).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stderr.write("[pay] " + (fmt % args) + "\n")


def cmd_serve(args: argparse.Namespace) -> None:
    srv = HTTPServer((args.host, args.port), Handler)
    print(f"listening on http://{args.host}:{args.port}/pay?amount=1.00&bank=901")
    srv.serve_forever()


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_form = sub.add_parser("form", help="生成自动提交的 HTML 表单文件")
    p_form.add_argument("--amount", default="1.00")
    p_form.add_argument("--bank", default="901")
    p_form.add_argument("--out", default="pay.html")
    p_form.set_defaults(func=cmd_form)

    p_serve = sub.add_parser("serve", help="启动 HTTP 服务 (GET /pay)")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8080)
    p_serve.set_defaults(func=cmd_serve)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
