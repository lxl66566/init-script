# ruff: noqa: F403, F405

import inspect
import logging
from collections import OrderedDict
from typing import Callable

from ..proxy import (
    config_caddy,
    config_hysteria,
    config_openppp2,
    config_trojan,
    config_trojan_go,
)
from ..utils import *
from ..utils.mycache import *
from ..var import ask, domain
from .fish import fish_add_config, install_fish_on_debian, post_install_fish
from .install_utils import *


class PackageList(OrderedDict):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def add(self, package: "Package"):
        self[package.name] = package


packages_list: PackageList["Package"] = PackageList()


class Package:
    """
    `pm_name`: 一个函数，根据当前架构与包管理器返回系统包名。
    `level`: 优先级，数字越大优先级越高。0 默认不安装，1 在配置充足的系统上安装，2 必定安装。
    `pre_install_fun`：自定义安装前函数，返回 None | bool。如果未设置或返回 False，使用 `pm_install` 安装，返回 None 不安装，否则使用 `install_fun` 安装。
    `install_fun`: 自定义安装函数。如果返回 False，改为使用 pm_install 安装。
    `post_install_fun`: 自定义安装后函数，主要进行一些配置。无论使用 pm_install 还是 install_fun 安装，都会执行这个函数。
    """

    __slots__ = (
        "name",
        "pm_name",
        "level",
        "pre_install_fun",
        "install_fun",
        "post_install_fun",
    )

    def __init__(self, name: str, level: int = 0, **kwargs) -> None:
        self.name = name
        self.level = level
        for k, v in kwargs.items():
            setattr(self, k, v)
        assert hasattr(self, "name"), "package name is required"
        self.install_fun = getattr(self, "install_fun", None)

    def __lt__(self, other: "Package"):
        return self.name < other.name

    def call_with_param_0_or_1(self, fun: Callable):
        """
        调用函数，如果函数有且只有一个参数，则将 self 作为参数传入，否则不传。
        """
        assert callable(fun), "fun must be a callable"
        args = inspect.signature(fun).parameters
        assert len(args) <= 1, "自定义函数必须只有 0 或 1 个参数，找到了 {} 个".format(
            len(args)
        )
        if len(args) == 1:
            return fun(self)
        else:
            return fun()

    @install_once(name="install")
    def install(self):
        cut()
        print(f"""开始安装 {colored(self.name, "green")}...""")

        name = getattr(self, "pm_name", lambda: self.name)()
        if not name:
            name = self.name

        pre_ret = self.call_with_param_0_or_1(
            getattr(self, "pre_install_fun", lambda: False)
        )

        if pre_ret is None:
            print(f"""{colored(self.name, 'green')} 不满足安装条件，安装取消.""")
            return

        if not pre_ret and check_package_exists(name):
            pm_install(name)
        else:
            assert hasattr(
                self, "install_fun"
            ), "跳过了系统包安装，并且找不到自定义安装函数。这可能是您的平台不受支持，或者包管理器版本过低，请开 issue 报告"
            fun = getattr(self, "install_fun")
            self.call_with_param_0_or_1(fun)

        self.call_with_param_0_or_1(getattr(self, "post_install_fun", lambda: None))

        print(f"""{colored(self.name, "green")} 安装完成.""")


def init():
    """
    init the package manager.
    """
    ask()
    match pm():
        case "p":
            assert exists("pacman")
            rc_sudo("pacman -Syu --noconfirm")
            rc_sudo("pacman -S --noconfirm archlinux-keyring")
            rc_sudo("pacman -S --needed --noconfirm base-devel")
        case "a":
            assert exists("apt")
            assert is_root(), "You need to be root to install packages."
            rc_sudo("apt-get remove apt-listchanges -y", check=False)
            rc_sudo("apt update -y")
            rc_sudo("DEBIAN_FRONTEND=noninteractive apt upgrade -y")
            if distro() == "d" and version() <= 11:
                rc(
                    "echo 'deb http://deb.debian.org/debian buster-backports main' >> /etc/apt/sources.list"
                )
                rc(
                    "echo 'deb https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/Debian_10/ /' > /etc/apt/sources.list.d/devel:kubic:libcontainers:stable.list"
                )
                rc(
                    "curl -L https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/Debian_10/Release.key | apt-key add -"
                )
                rc("apt-get update -y")
                rc("apt upgrade -y")
                rc("apt-get -y -t buster-backports install libseccomp2")
        case "y":
            assert exists("yum"), "yum is not installed"
            assert is_root(), "You need to be root to install packages."
            rc_sudo("yum update -y")
        case _:
            error_exit("Unsupported package manager.")

    logging.info("init success")
    install_all()


def pacman(*args):
    rc_sudo(" ".join(("pacman", "-S", "--needed", "--noconfirm", *args)))


def paru(*args):
    assert not is_root(), "paru must be run as non-root user"
    rc(" ".join(("yes | paru -S --needed", *args)))


def day(*args):
    """
    dnf + apt + yum 3 in 1
    """
    rc_sudo(
        " ".join(
            (
                "NEEDRESTART_MODE=a",  # for ubuntu
                "DEBIAN_FRONTEND=noninteractive",  # for debian
                {"a": "apt", "y": "yum", "d": "dnf"}.get(pm()),
                "install -y",
                quiet(),
                *args,
            )
        )
    )


def pm_install(*args) -> bool:
    """
    basically install any packages by pm
    actually it's pacman + dnf + apt + yum 4 in 1
    """
    logging.info("开始安装：" + " ".join(args))
    match pm():
        case "p":
            pacman(*args)
        case _:
            day(*args)
    logging.info("安装完成：" + " ".join(args))
    return True


def cargo(*args):
    if exists("cargo"):
        rc_sudo(" ".join(("cargo install --locked", *args)))
    else:
        packages_list["cargo"].install()


def pip(*args):
    """
    use pip to install packages.
    """

    def rc_no_err(command):
        return (
            rc(command, stderr=subprocess.DEVNULL) if not debug_mode() else rc(command)
        )

    if not exists("pip") and not exists("pip3"):
        packages_list["python-pip"].install()

    command = [sys.executable, "-m", "pip", "install"]
    command.extend(args)
    command = " ".join(command)
    try:
        rc_no_err(command)
    except subprocess.CalledProcessError:
        try:
            command += " --break-system-packages"
            rc_no_err(command)
        except subprocess.CalledProcessError:
            error_exit("pip 安装失败，请检查系统")


def bpm(*args):
    "use bpm to install"
    if exists("bpm"):
        rc_sudo(" ".join(("bpm", "i", quiet(), *args)))
    else:
        packages_list["bpm"].install()


def pre_install_proxy(need_caddy=True):
    if not domain():
        print("未设置域名，跳过安装")
        return None
    if need_caddy and not exists("caddy"):
        packages_list["caddy"].install()
    return False


# region begin install


# default packages.
for i in [
    "sudo",
    "wget",
    "curl",
    "rsync",
    "btop",
    "lsof",
    "ncdu",
    "tldr",
    "podman",
    "fzf",
    "make",
]:
    packages_list.add(Package(i, 2))


def pre_install_paru():
    try:
        assert distro() == "a", "Only support Arch Linux"
        assert not is_root(), "installing paru must not be root"
        assert exists("git"), "Git not found"
        assert exists("makepkg"), "Makepkg not found"
    except AssertionError:
        return None
    return True


# not used: i do not need AUR now.
def install_paru():
    if exists("paru"):
        return
    rc(
        "git clone https://aur.archlinux.org/paru-bin.git --depth=1",
        cwd="/tmp",
    )
    rc("makepkg -si")


packages_list.add(
    Package(
        "paru",
        0,
        pre_install_fun=pre_install_paru,
        install_fun=install_paru,
    )
)


packages_list.add(
    Package(
        "trojan",
        level=1,
        pre_install_fun=lambda: pre_install_proxy(True),
        post_install_fun=config_trojan,
    )
)


def cron_name():
    if pm() == "p":
        return "cronie"
    else:
        return "cron"


def post_install_cron(self: Package):
    rc_sudo(f"systemctl enable --now {self.name}")


packages_list.add(
    Package(
        "cron",
        2,
        pm_name=cron_name,
        post_install_fun=post_install_cron,
    )
)


def base_name():
    if pm() == "p":
        return "base-devel"
    elif pm() == "a":
        return "build-essential"


def install_base():
    """
    为了之后的 nvim 插件做准备，300MB，不想装可以不用
    """
    if pm() == "y":
        rc_sudo(
            " ".join(
                (
                    "yum",
                    "groupinstall",
                    "'Development Tools'",
                    "-y",
                    quiet(),
                )
            )
        )


packages_list.add(
    Package(
        "base",
        1,
        pm_name=base_name,
        pre_install_fun=lambda: pm() not in "ap",
        install_fun=install_base,
    )
)

packages_list.add(
    Package(
        "python-requests",
        0,
        pm_name=lambda: "python-requests" if pm() == "p" else "python3-requests",
    )
)
packages_list.add(
    Package(
        "python-pip",
        2,
        pm_name=lambda: "python-pip" if pm() == "p" else "python3-pip",
    )
)
packages_list.add(
    Package(
        "pipx",
        0,
        pm_name=lambda: "python-pipx" if pm() == "p" else "pipx",
        post_install_fun=lambda: rc_sudo("pipx ensurepath"),
        # rc("fish_add_path ~/.local/bin")
    )
)
packages_list.add(
    Package(
        "bpm",
        2,
        pre_install_fun=lambda: True,
        install_fun=lambda: pip(
            "bin-package-manager", "" if not exists("bpm") else " -U"
        ),
    )
)
packages_list.add(
    Package(
        "trojan-go",
        2,
        pre_install_fun=lambda: None if pre_install_proxy() is None else True,
        install_fun=lambda: bpm("https://github.com/p4gefau1t/trojan-go"),
        post_install_fun=config_trojan_go,
    )
)


def pre_install_caddy():
    if domain() is None:
        return None

    if pm() == "a":
        day("debian-keyring", "debian-archive-keyring", "apt-transport-https")
        rc(
            "curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg"
        )
        rc(
            "curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list"
        )
        rc_sudo("apt update")
    elif pm() == "y":
        day("yum-plugin-copr")
        rc_sudo("yum copr enable @caddy/caddy")
    return False


packages_list.add(
    Package(
        "caddy",
        2,
        pre_install_fun=pre_install_caddy,
        install_fun=lambda: bpm("caddy"),
        post_install_fun=config_caddy,
    )
)

packages_list.add(
    Package(
        "hysteria2",
        2,
        pre_install_fun=lambda: None if pre_install_proxy() is None else True,
        install_fun=lambda: rc_sudo("curl -fsSL https://get.hy2.sh/ | bash"),
        post_install_fun=config_hysteria,
    )
)

packages_list.add(
    Package(
        "fd",
        2,
        pre_install_fun=lambda: pm() != "p",
        install_fun=lambda: bpm("https://github.com/sharkdp/fd"),
    )
)

packages_list.add(
    Package(
        "mcfly",
        0,
        pre_install_fun=lambda: pm() != "p",
        install_fun=lambda: rc_sudo(
            "curl -LSfs https://raw.githubusercontent.com/cantino/mcfly/master/ci/install.sh | sh -s -- --git cantino/mcfly --force"
        ),
        post_install_fun=lambda: fish_add_config("mcfly init fish | source"),
    )
)


packages_list.add(
    Package(
        "zoxide",
        2,
        pre_install_fun=lambda: distro() == "d" and version() < 11,
        install_fun=lambda: rc_sudo(
            "curl -sS https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | bash"
        ),
        post_install_fun=lambda: fish_add_config("zoxide init fish | source"),
    )
)


packages_list.add(
    Package(
        "fish",
        2,
        pre_install_fun=lambda: distro() == "d" and version() < 11,
        install_fun=install_fish_on_debian,
        post_install_fun=post_install_fish,
    )
)

packages_list.add(
    Package(
        "starship",
        level=2,
        pre_install_fun=lambda: pm() != "p",
        install_fun=lambda: rc_sudo(
            "curl -sS https://starship.rs/install.sh | sh -s -- -y"
        ),
        post_install_fun=lambda: fish_add_config("starship init fish | source"),
    )
)

packages_list.add(
    Package(
        "cargo",
        level=2,
        install_fun=lambda: rc_sudo("curl https://sh.rustup.rs -sSf | sh -s -- -y"),
    )
)

packages_list.add(
    Package(
        "sd",
        level=2,
        pm_name=lambda: "sd" if pm() == "p" else "rust-sd",
        pre_install_fun=lambda: (distro() == "d" and version() < 13) or distro() == "u",
        install_fun=lambda: bpm("https://github.com/chmln/sd"),
    )
)

packages_list.add(
    Package(
        "ripgrep",
        level=2,
        pre_install_fun=lambda: pm() != "p",
        install_fun=lambda: bpm("https://github.com/BurntSushi/ripgrep", "-b rg"),
    )
)

packages_list.add(
    Package(
        "eza",
        level=2,
        pre_install_fun=lambda: pm() != "p",
        install_fun=lambda: bpm("https://github.com/eza-community/eza"),
    )
)


def install_yazi():
    if pm() == "p":
        pacman("yazi", "ffmpegthumbnailer", "unarchiver", "jq", "poppler")
    else:
        bpm("https://github.com/sxyazi/yazi")


packages_list.add(
    Package(
        "yazi",
        level=2,
        install_fun=install_yazi,
    )
)

packages_list.add(
    Package(
        "neovim",
        level=2,
        pre_install_fun=lambda: pm() != "p",
        install_fun=lambda: bpm("https://github.com/neovim/neovim"),
    )
)

packages_list.add(
    Package(
        "fastfetch",
        level=2,
        pre_install_fun=lambda: pm() != "p",
        install_fun=lambda: bpm("https://github.com/fastfetch-cli/fastfetch"),
    )
)

packages_list.add(
    Package(
        "zellij",
        level=2,
        pre_install_fun=lambda: pm() != "p",
        install_fun=lambda: bpm("https://github.com/zellij-org/zellij"),
    )
)

packages_list.add(
    Package(
        "bat",
        level=2,
        pre_install_fun=lambda: pm() != "p",
        install_fun=lambda: bpm("https://github.com/sharkdp/bat"),
    )
)

packages_list.add(
    Package(
        "xh",
        level=2,
        pre_install_fun=lambda: pm() != "p",
        install_fun=lambda: bpm("https://github.com/ducaale/xh"),
    )
)


packages_list.add(
    Package(
        "openppp2",
        level=2,
        pre_install_fun=lambda: True,
        install_fun=lambda: bpm(
            "https://github.com/liulilittle/openppp2",
            "-b ppp",
            "--filter uring" if kernel_ver() > 5.10 else "",
        ),
        post_install_fun=config_openppp2,
    )
)

packages_list.add(
    Package(
        "atuin",
        level=2,
        pre_install_fun=lambda: pm() != "p",
        install_fun=lambda: bpm("https://github.com/atuinsh/atuin"),
        post_install_fun=lambda: (
            rc("atuin import auto"),
            fish_add_config("atuin init fish | source"),
        ),
    )
)


def install_all():
    cut()
    logging.info(colored("starting to install ALL", "green"))
    for item in packages_list.values():
        item.install()
    cut()
    logging.info("all packages have been installed")


def show_all_available_packages():
    def _colored_s(iter):
        return map(
            lambda x: colored(x, "red")
            if x in ("hysteria2", "openppp2", "trojan", "trojan-go")
            else colored(x, "green"),
            iter,
        )

    print(
        colored("可用软件包", "green") + colored("标红为代理软件：", "red"),
        ", ".join(_colored_s(packages_list.keys())),
    )


def install_one(p: str, ignore_cache: bool = False):
    try:
        if ignore_cache:
            mycache("install").remove_set(p)
        packages_list[p].install()
    except (TypeError, KeyError):
        trace()
        error_exit(f"脚本未收录软件：{p}")
    except KeyboardInterrupt:
        error_exit("退出脚本")


def ask_install_one():
    show_all_available_packages()
    temp = (
        user_input("请输入安装软件名，以空格隔开，输入 -y 无视缓存安装：")
        .strip()
        .split(" ")
    )
    if not temp or not temp[0]:
        error_exit("未输入内容")
    flag = False
    if "-y" in temp:
        temp.remove("-y")
        flag = True
    for i in temp:
        install_one(i, flag)
