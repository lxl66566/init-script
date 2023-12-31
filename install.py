# ruff: noqa: F403, F405

import logging
from copy import copy
from functools import lru_cache
from itertools import chain
from pathlib import Path

from mycache import *
from ufcs import UFCS
from utils import *

# 多发行版通用的安装列表
my_install_list = [
    "sudo",
    "wget",
    "curl",
    "rsync",
    "unzip",
    "make",
    "btop",
    "lsof",
    "zoxide",
    "fzf",
    "ncdu",
    "tldr",
    "trojan",
    "podman",
]
TEMP_NAME = "initscript"
TEMP_PATH = Path("/tmp") / TEMP_NAME


def init():
    match pm():
        case "p":
            assert exists("pacman")
            rc_sudo("pacman -Syu --noconfirm")
            rc_sudo("pacman -S --noconfirm archlinux-keyring")
            rc_sudo("pacman -S --needed --noconfirm base-devel")
        case "a":
            assert exists("apt")
            assert is_root(), "You need to be root to install packages."
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

    logging.info("init success")
    install_all()


def quiet() -> str:
    """
    do you need quiet?
    """
    if debug_mode():
        return ""
    else:
        return "-q"


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


def basic_install(*args) -> bool:
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
        install_cargo()


# do not use it, it cannot work.
def lastversion(s: str, bin_name: str = ""):
    """
    install something via lastversion
    :param s: github repo
    :param bin_name: executable binary filename parse to install_from_file
    """
    if not exists("lastversion"):
        install_python_lastversion()
    assert exists("lastversion"), "lastversion not installed"
    rc(f"lastversion {s} --assets -yv -d {TEMP_PATH}.tmp")
    rc(f"tar -xaf {TEMP_NAME}.tmp --one-top-level={TEMP_NAME}", cwd="/tmp")
    install_from_file(bin_name or s.rpartition("/")[-1])


@log
@mycache_once(name="install")
def config_fish():
    dotfile = mypath() / "dotfile"
    branch = "archlinux"
    if not dotfile.exists():
        rc(
            f"git clone https://github.com/lxl66566/dotfile.git -b {branch} --depth 1",
            cwd=mypath(),
        )
    else:
        rc(f"git fetch --all {quiet()} -f", cwd=dotfile)
        rc(f"git reset --hard origin/{branch}", cwd=dotfile)
    rc(f"cp -rf {dotfile}/home/absolutex/.config/fish ~/.config", cwd=mypath())


@log
@mycache_once(name="install")
def install_my_list():
    basic_install(*my_install_list)


# because AUR has a lot of problems, i decide to install them manually instead of AUR
@log
@mycache_once(name="install")
def install_paru():
    assert distro() == "a", "Only support Arch Linux"
    assert not is_root(), "installing paru must not be root"
    assert exists("git"), "Git not found"
    assert exists("makepkg"), "Makepkg not found"

    if exists("paru"):
        return
    rc(
        "git clone https://aur.archlinux.org/paru-bin.git --depth=1",
        cwd="/tmp",
    )
    rc("makepkg -si")


@log
@mycache_once(name="install")
def install_cron():
    match pm():
        case "p":
            pacman("cronie")
            rc_sudo("systemctl enable --now cronie")
        case _:
            basic_install("cron")
            rc_sudo("systemctl enable --now cron")


@log
@mycache_once(name="install")
def install_base():
    """
    为了之后的 nvim 插件做准备，300MB，不想装可以不用
    """
    match pm():
        case "p":
            pacman("base-devel")
        case "a":
            day("build-essential")
        case "y":
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


@log
@mycache_once(name="install")
def install_python_requests():
    match pm():
        case "p":
            basic_install("python-requests")
        case _:
            basic_install("python3-requests")


def install_from_file(bin_name: str):
    logging.info("installing...")
    p = TEMP_PATH
    if not bin_name:
        logging.error("lossing bin_name when install from file")
    if isinstance(p, str):
        p = Path(p)
    temp = chain(p.rglob("*.fish"), p.rglob("*.service"))
    for i in chain(p.rglob(bin_name), temp) if bin_name else temp:
        if not i.is_file():
            continue
        match i.suffix:
            case "":
                rc_sudo(f"install -Dm755 {str(i.absolute())} /usr/bin/{i.name}")
            case ".fish":
                rc_sudo(
                    f"install -Dm644 {str(i.absolute())} /usr/share/fish/vendor_completions.d/{i.name}"
                )
            case ".service":
                rc_sudo(
                    f"install -Dm644 {str(i.absolute())} /usr/lib/systemd/system/{i.name}"
                )
        logging.info(f"installed {i.name}")


def install_from_dir_all(to_: Path, from_: Path = TEMP_PATH):
    """
    install all files from this dir to another dir
    make sure that there's no additional file on the /tmp/{TEMP_NAME}
    """
    if isinstance(to_, str):
        to_ = Path(to_)
    if isinstance(from_, str):
        from_ = Path(from_)
    if not to_.is_dir():
        error_exit(f"{to_} is not a existing directory")
    for i in from_.rglob("*"):
        if not i.is_file():
            continue
        dest_path = to_ / i.relative_to(from_)
        rc_sudo(f"install -Dm755 {str(i.absolute())} {str(dest_path)}")
        logging.info(f"installed {i.name} to {str(dest_path)}")


def unzip(__type: str):
    # 先删除上次安装缓存，否则会出事，解压的文件会混在一起
    rc(f"rm -rf {TEMP_PATH}", cwd="/tmp")

    match __type:
        case "zip":
            assert exists("unzip"), "unzip not found"
            rc(f"unzip -o {quiet()} {TEMP_NAME}.tmp -d {TEMP_NAME}", cwd="/tmp")
        case "tar":
            rc(f"tar -xaf {TEMP_NAME}.tmp --one-top-level={TEMP_NAME}", cwd="/tmp")
        case _:
            error_exit(f"file with type `{__type}` cannot successfully extracted")


def download_gh_release(s: str, package_name: str = ""):
    """
    install newest package from github release
    :param s: `<author>/<repo>`, like `eza-community/eza`
    :param bin_name: the binary file in this release, like `eza`. use the `<repo>` name default.
    :param package_name: if cannot automatically find the correct package in the release, you may need to specify that.
    """
    import requests

    @lru_cache
    def n(s):
        return s.rpartition("/")[-1]

    logging.info(f"downloading from github: {s}")

    response = requests.get(f"https://api.github.com/repos/{s}/releases/latest")
    dl_links = (
        UFCS([i for i in response.json().get("assets")])
        .filter(lambda x: x.get("size") > 100)
        .map(lambda x: x.get("browser_download_url"))
    )
    assert list(dl_links), "no release found"

    url = (
        dl_links.filter(lambda x: "linux" in n(x).lower())
        .filter(  # now only accept tar.gz and zip.
            lambda x: n(x).lower().endswith("tar.gz") or n(x).lower().endswith("zip")
        )
        .sorted(key=lambda x: "musl" not in n(x))
        .sorted(key=lambda x: n(x).endswith("tar.gz"))  # 优先使用 musl，zip
        .sorted(key=lambda x: "x86_64" not in n(x) and "amd64" not in n(x).lower())
        .list()
    )
    if not url and not package_name:
        url = UFCS(dl_links).filter(lambda x: package_name in n(x)).list()
    assert url, "no release found"
    url = url[0]

    logging.info(f"downloading from {url}")
    rc(f"wget -N {quiet()} {url} -O {TEMP_PATH}.tmp", cwd="/tmp")
    if url.rstrip("/").endswith(".zip"):
        unzip("zip")
    else:
        unzip("tar")


def github(s: str):
    """
    install a repo from github binary release.
    :param s: github repo, `<author>/<repo>`
    """
    temp = s.rpartition("/")[-1]
    download_gh_release(s)
    install_from_file(temp)


@log
@mycache_once(name="install")
def install_python_pip():
    match pm():
        case "p":
            pacman("python-pip")
        case _:
            day("python3-pip")


@log
@mycache_once(name="install")
def install_python_pipx():
    match pm():
        case "p":
            pacman("python-pipx")
        case _:
            day("pipx")
    rc("fish_add_path ~/.local/bin")


@log
@mycache_once(name="install")
def install_python_lastversion():
    if not exists("pipx"):
        install_python_pipx()
    rc("pipx install lastversion")
    rc("pipx ensurepath")


@log
@mycache_once(name="install")
def install_trojan_go():
    download_gh_release("p4gefau1t/trojan-go")
    install_from_file("trojan-go")
    rc("mkdir -p /etc/trojan-go")


@log
@mycache_once(name="install")
def install_caddy():
    match pm():
        case "p":
            pacman("caddy")
        case "a":
            day("debian-keyring", "debian-archive-keyring", "apt-transport-https")
            rc(
                "curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg"
            )
            rc(
                "curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list"
            )
            rc_sudo("apt update")
            basic_install("caddy")
        case "y":
            day("yum-plugin-copr")
            rc_sudo("yum copr enable @caddy/caddy")
            basic_install("caddy")


@log
@mycache_once(name="install")
def install_hysteria():
    rc_sudo("curl -fsSL https://get.hy2.sh/ | bash")


@log
@mycache_once(name="install")
def install_fd():
    match pm():
        case "p":
            pacman("fd")
        case "a":
            github("sharkdp/fd")


@log
@mycache_once(name="install")
def install_mcfly():
    match distro():
        case "a":
            pacman("mcfly")
        case _:
            rc_sudo(
                "curl -LSfs https://raw.githubusercontent.com/cantino/mcfly/master/ci/install.sh | sh -s -- --git cantino/mcfly --force"
            )


@log
@mycache_once(name="install")
def install_zoxide():
    match distro():
        case "a":
            pacman("zoxide")
        case _:
            if distro() == "d" and version() < 11:
                rc_sudo(
                    "curl -sS https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | bash"
                )
            else:
                basic_install("zoxide")


@log
@mycache_once(name="install")
def install_fish():
    match pm():
        case "p":
            pacman("fish")
        case "a":
            if distro() == "d" and version() < 11:
                url = "https://download.opensuse.org/repositories/shells:/fish:/nightly:/master/Debian_10/amd64/"
                package_name = rc(
                    f"""curl {url} | grep -Po "fish_3\..*?\.deb?" | tail -1""",
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                rc(f"wget {url}{package_name}", cwd="/tmp")
                rc_sudo("dpkg -i " + package_name, cwd="/tmp")
            else:
                basic_install("fish")
    rc_sudo("chsh -s /usr/bin/fish")


@log
@mycache_once(name="install")
def install_starship():
    match distro():
        case "a":
            pacman("starship")
        case _:
            rc_sudo("curl -sS https://starship.rs/install.sh | sh -s -- -y")


@log
@mycache_once(name="install")
def install_cargo():
    if exists("cargo"):
        return
    basic_install("cargo")
    #         rc_sudo("curl https://sh.rustup.rs -sSf | sh -s -- -y")


@log
@mycache_once(name="install")
def install_sd():
    match pm():
        case "p":
            pacman("sd")
        case "a":
            if (distro() == "d" and version() < 13) or distro() == "u":
                github("chmln/sd")
            else:
                basic_install("rust-sd")


@log
@mycache_once(name="install")
def install_rg():
    match pm():
        case "p":
            pacman("ripgrep")
        case "a":
            if (distro() == "d" and version() < 12) or (
                distro() == "u" and version() < 18.10
            ):
                rc(
                    "wget https://github.com/BurntSushi/ripgrep/releases/download/13.0.0/ripgrep_13.0.0_amd64.deb",
                    cwd="/tmp",
                )
                rc_sudo("dpkg -i /tmp/ripgrep_13.0.0_amd64.deb")
            else:
                basic_install("ripgrep")
        case _:
            github("BurntSushi/ripgrep")


@log
@mycache_once(name="install")
def install_eza():
    match pm():
        case "p":
            pacman("eza")
        case _:
            github("eza-community/eza")


@log
@mycache_once(name="install")
def install_yazi():
    match distro():
        case "a":
            pacman("yazi", "ffmpegthumbnailer", "unarchiver", "jq", "poppler")
        case _:
            # github("sxyazi/yazi")
            # github api 无法获取 pre-release，因此手动下载。
            yazi_name = "yazi-x86_64-unknown-linux-gnu"
            rc(
                f"wget -N {quiet()} https://github.com/sxyazi/yazi/releases/download/v0.1.5/{yazi_name}.zip -O {TEMP_PATH}.tmp",
                cwd="/tmp",
            )
            unzip("zip")
            install_from_file("yazi")


@log
@mycache_once(name="install")
def install_neovim():
    match distro():
        case "a":
            pacman("neovim")
        case _:
            __name = "nvim-linux64"
            download_gh_release("neovim/neovim", __name)
            install_from_dir_all(
                to_="/usr",
                from_=TEMP_PATH / __name,
            )


@log
@mycache_once(name="install")
def install_fastfetch():
    match pm():
        case "p":
            pacman("fastfetch")
        case _:
            github("fastfetch-cli/fastfetch")


@log
@mycache_once(name="install")
def install_zellij():
    match pm():
        case "p":
            pacman("zellij")
        case _:
            github("zellij-org/zellij")


@log
@mycache_once(name="install")
def install_bat():
    match pm():
        case "p":
            pacman("bat")
        case _:
            github("sharkdp/bat")


@log
@mycache_once(name="install")
def install_xh():
    match pm():
        case "p":
            pacman("xh")
        case _:
            github("ducaale/xh")


# 函数映射和是否自动安装
others = {
    "python_requests": (install_python_requests, True),
    "fish": (install_fish, True),
    "base": (install_base, True),
    "mcfly": (install_mcfly, True),
    "starship": (install_starship, True),
    "eza": (install_eza, True),
    "config_option": (config_fish, True),
    "cron": (install_cron, True),
    "caddy": (install_caddy, True),
    "trojan-go": (install_trojan_go, True),
    "hysteria": (install_hysteria, True),
    "fd": (install_fd, True),
    "sd": (install_sd, True),
    "rg": (install_rg, True),
    "yazi": (install_yazi, True),
    "neovim": (install_neovim, True),
    "fastfetch": (install_fastfetch, True),
    "zellij": (install_zellij, True),
    "pip": (install_python_pip, False),
    "pipx": (install_python_pipx, False),
    "lastversion": (install_python_lastversion, False),
    "cargo": (install_cargo, False),
    "paru": (install_paru, False),
    "bat": (install_bat, True),
    "xh": (install_xh, True),
}


def install_all():
    cut()
    logging.info(colored("starting to install ALL", "green"))
    install_my_list()
    for p, auto in others.values():
        if auto:
            p()
    cut()
    logging.info("all packages have been installed")


def show_all_available_packages():
    print("可用软件包：")
    temp = copy(my_install_list)
    temp.extend(others.keys())
    UFCS(temp).sorted().print()


def install_one(p: str, ignore_cache: bool = False):
    if p in my_install_list:
        basic_install(p)
        return
    try:
        func = others.get(p)[0]
        if ignore_cache:
            mycache("install").remove_set(func.__name__)
        func()
    except TypeError:
        error_exit(f"脚本未收录软件：{p}")
    except KeyboardInterrupt:
        error_exit("退出脚本")
