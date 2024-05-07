"""
包含一些需要使用的变量。
"""

import logging as log
from pathlib import Path
from typing import Optional

from .utils import colored
from .utils.input import user_input
from .utils.mycache import BaseCache

# 在这里更改自定义配置

# 默认代理端口
PROXY_PORT = {
    "openppp2": 29777,
    "hysteria": 30000,
    "trojan-go": 40000,
    "trojan": 50000,
}
# fishshell 配置默认路径
FISH_CONFIG_FILE_PATH = Path.home() / ".config" / "fish" / "config.fish"
GET_CERT_MAX_RETRY = 4  # 获取证书的最大重试次数
GET_CERT_DEFAULT_WAIT = 20  # 获取证书的默认等待时间（秒）

# 自定义配置区域结束，不要更改其他地方

_cache: dict = BaseCache("var").load() or {}
_domain: Optional[str] = _cache.get("domain")
_password: list[str] = _cache.get("password") or []

log.debug(f"read domain: {_domain}, password: {_password}")


def save():
    _cache["domain"] = _domain
    _cache["password"] = _password
    BaseCache("var").save(_cache)


def reset():
    global _cache
    _cache.clear()
    log.info("已重置域名与密码。")


def ask():
    global _domain, _password

    if not _domain:
        _domain = user_input(
            f"请输入本机域名，若留空则跳过所有{colored('需要 SSL 的代理', 'yellow')}部署: "
        )
        print(f"使用域名：`{_domain}`")
    if not _domain:
        return
    if not _password:
        _password = user_input(
            "请输入密码，不同密码用空格隔开，用于设置代理。在某些场合下只有第一个密码有效: "
        ).split(" ")
    assert _password, "密码不能为空"
    print(f"使用密码：`{_password}`")
    save()


def domain():
    return _domain


def password():
    return _password
