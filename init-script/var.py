"""
包含一些需要使用的变量。
"""

import logging as log
from pathlib import Path

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


class DomainPassword:
    """
    cache
    """

    def __init__(self, test=False):
        self.base_cache = BaseCache("var", test)
        self.c = self.base_cache.load() or {}
        log.debug(f"read domain: {self.domain()}, password: {self.password()}")

    def save(self):
        self.base_cache.save(self.c)

    def clear(self):
        self.c.pop("domain", None)
        self.c.pop("password", None)
        self.save()
        log.info("已重置域名与密码。")

    def ask(self):
        if not self.domain():
            self.set_domain(
                user_input(
                    f"请输入本机域名，若留空则跳过所有{colored('需要 SSL 的代理', 'yellow')}部署: "
                ).strip()
            )
            log.info(f"使用域名：`{self.domain()}`")
        if not self.domain():
            log.info("已清空域名。")
            return
        if not self.password():
            self.set_password(
                user_input(
                    "请输入密码，不同密码用空格隔开，用于设置代理。在某些场合下只有第一个密码有效: "
                )
                .strip()
                .split(" ")
            )
        assert self.password(), "密码不能为空"
        log.info(f"使用密码：`{self.password()}`")
        self.save()

    def domain(self):
        return self.c.get("domain")

    def password(self):
        return self.c.get("password") or []

    def set_domain(self, domain):
        self.c["domain"] = domain
        self.save()

    def set_password(self, password):
        self.c["password"] = password
        self.save()
