"""
包含一些需要使用的变量。
"""

from typing import Optional

from .utils import user_input
from .utils.mycache import mycache

_cache: dict = mycache("var").load() or {}

_domain: Optional[str] = _cache.get("domain")
_password: list[str] = _cache.get("password") or []

PROXY_PORT = {
    "openppp2": 29777,
    "hysteria": 30000,
    "trojan-go": 40000,
    "trojan": 50000,
}


def save():
    _cache["domain"] = _domain
    _cache["password"] = _password
    mycache("var").save(_cache)


def ask():
    global _domain, _password

    if not _domain:
        _domain = user_input("请输入本机域名，若留空则跳过所有需要 SSL 的代理部署: ")
    if not _domain:
        return
    if not _password:
        _password = user_input(
            "请输入密码，不同密码用空格隔开，用于设置代理。在某些场合下只有第一个密码有效: "
        ).split(" ")
    assert _password, "密码不能为空"
    save()


def domain():
    return _domain


def password():
    return _password
