import logging
from pathlib import Path
from subprocess import run

from utils import *

mypath = ""
distro = ""
version = 6.0

# 多发行版通用的安装列表
my_install_list = [
    "sudo",
    "wget",
    "curl",
    "btop",
    "lsof",
    "zoxide",
    "fzf",
    "ncdu",
    "tldr",
    "trojan",
    "podman",
    "neovim",
    "unzip",
]


def get_info(main_path, distro_name, version_name):
    global mypath, distro, version
    mypath = main_path
    distro = distro_name
    version = float(version_name)


def init(*args):
    get_info(*args)
    match distro:
        case "a":
            assert exists("pacman")
            rc_sudo("pacman -Syu --noconfirm")
            rc_sudo("pacman -S --noconfirm archlinux-keyring")
            rc_sudo("pacman -S --needed --noconfirm base-devel")
        case "d" | "u":
            assert exists("apt")
            assert is_root(), "You need to be root to install packages."
            rc_sudo("apt update -y")
            rc_sudo("DEBIAN_FRONTEND=noninteractive apt upgrade -y")
            if version <= 11:
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
    logging.info("init success")
    cut()
    logging.info("starting to install all")
    install_all()


def pacman(*args):
    rc_sudo(" ".join(("pacman", "-S", "--needed", "--noconfirm", *args)))


def paru(*args):
    assert not is_root(), "paru must be run as non-root user"
    rc(" ".join(("yes | paru -S --needed", *args)))


def apt(*args):
    rc_sudo(" ".join(("apt", "install", "-y", *args)))


def cargo(*args):
    if exists("cargo"):
        rc_sudo(" ".join(("cargo install --locked", *args)))
    else:
        install_cargo()


def install_mylist(l: list[str]):
    match distro:
        case "a":
            pacman(*l)
        case "d" | "u":
            apt(*l)
    logging.info("install mylist success: {}".format(" ".join(l)))


def config():
    if not (Path(mypath) / "dotfile").exists():
        rc(
            "git clone https://github.com/lxl66566/dotfile.git -b archlinux --depth 1",
            cwd=mypath,
        )
    dotfile = mypath.rstrip("/") + "/dotfile"
    rc(f"cp -rf {dotfile}/home/absolutex/.config ~", cwd=mypath)
    logging.info("copy config dotfile success")


# because AUR has a lot of problems, i decide to install them manually instead of AUR
def install_paru():
    assert distro == "a", "Only support Arch Linux"
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
    logging.info("install paru success")


def install_cron():
    match distro:
        case "a":
            pacman("cronie")
            rc_sudo("systemctl enable --now cronie")
        case "d" | "u":
            apt("cron")
            rc("systemctl enable --now cron")
    logging.info("install cron success")


def install_trojan_go():
    assert exists("unzip"), "unzip not found"
    rc(
        "wget https://github.com/p4gefau1t/trojan-go/releases/latest/download/trojan-go-linux-amd64.zip",
        cwd="/tmp",
    )
    rc("unzip trojan-go-linux-amd64.zip -d /tmp/trojan-go", cwd="/tmp")
    rc_sudo("install -Dm 755 '/tmp/trojan-go/trojan-go' '/usr/bin/trojan-go'")
    rc_sudo(
        "install -Dm 644 '/tmp/trojan-go/example/trojan-go.service' '/usr/lib/systemd/system/trojan-go.service'"
    )
    rc_sudo(
        "install -Dm 644 '/tmp/trojan-go/example/trojan-go@.service' '/usr/lib/systemd/system/trojan-go@.service'"
    )
    rc("mkdir -p /etc/trojan-go")
    logging.info("install trojan-go success")


def install_caddy():
    match distro:
        case "a":
            pacman("caddy")
        case _:
            apt("debian-keyring", "debian-archive-keyring", "apt-transport-https")
            rc(
                "curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg"
            )
            rc(
                "curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list"
            )
            rc("apt update")
            apt("caddy")
    logging.info("install caddy success")


def install_hysteria():
    rc_sudo("curl -fsSL https://get.hy2.sh/ | bash")
    logging.info("install hysteria success")


def install_fd():
    match distro:
        case "a":
            pacman("fd")
        case "d" | "u":
            assert exists("fish"), "fishshell must been installed"
            apt("fd-find")
            rc("fish -c 'alias fd fdfind'")
            # 但是并没有写入。。我也不知道为啥 alias 没生效。
            # rc("fish -c 'funcsave fd'")
    logging.info("fd success installed")


def install_mcfly():
    match distro:
        case "a":
            pacman("mcfly")
        case _:
            rc_sudo(
                "curl -LSfs https://raw.githubusercontent.com/cantino/mcfly/master/ci/install.sh | sh -s -- --git cantino/mcfly"
            )
    logging.info("install mcfly success")


def install_zoxide():
    match distro:
        case "a":
            pacman("zoxide")
        case _:
            if version < 11:
                rc_sudo(
                    "curl -sS https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | bash"
                )
            else:
                apt("zoxide")
    logging.info("install zoxide success")


def install_fish():
    match distro:
        case "a":
            pacman("fish")
        case "d":
            if version < 11:
                url = "https://download.opensuse.org/repositories/shells:/fish:/nightly:/master/Debian_10/amd64/"
                package_name = rc(
                    f"""curl {url} | grep -Po "fish_3\..*?\.deb?" | tail -1""",
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                rc(f"wget {url}{package_name}", cwd="/tmp")
                rc_sudo("dpkg -i " + package_name, cwd="/tmp")
            else:
                apt("fish")
        case "u":
            apt("fish")
    rc_sudo("chsh -s /usr/bin/fish")
    logging.info("fish installed")


def install_starship():
    match distro:
        case "a":
            pacman("starship")
        case "d" | "u":
            rc_sudo("curl -sS https://starship.rs/install.sh | sh -s -- -y")
    logging.info("starship installed")


# 不要上当！！！这不是 cargo 的安装！
def install_cargo():
    if exists("cargo"):
        return
    match distro:
        case "a":
            pacman("cargo")
        case _:
            rc_sudo("curl https://sh.rustup.rs -sSf | sh -s -- -y")


def install_sd():
    sd_version = "1.0.0"
    sd_name = f"sd-v{sd_version}-x86_64-unknown-linux-musl"
    match distro:
        case "a":
            pacman("sd")
        case "d":
            if version < 13:
                rc(
                    f"wget https://github.com/chmln/sd/releases/download/v{sd_version}/{sd_name}.tar.gz",
                    cwd="/tmp",
                )
                rc(
                    f"tar -xvaf /tmp/{sd_name}.tar.gz",
                    cwd="/tmp",
                )
                rc_sudo(f"install -Dm755 '/tmp/{sd_name}/sd' '/usr/bin/sd'")
                rc_sudo(
                    f"install -Dm644 '/tmp/{sd_name}/completions/sd.fish' '/usr/share/fish/vendor_completions.d/sd.fish'"
                )
            else:
                apt("rust-sd")
        case "u":
            apt("rust-sd")
    logging.info("sd installed")


def install_rg():
    match distro:
        case "a":
            pacman("ripgrep")
        case "d" | "u":
            if (distro == "d" and version < 12) or (distro == "u" and version < 18.10):
                rc(
                    "wget https://github.com/BurntSushi/ripgrep/releases/download/13.0.0/ripgrep_13.0.0_amd64.deb",
                    cwd="/tmp",
                )
                rc_sudo("dpkg -i /tmp/ripgrep_13.0.0_amd64.deb")
            else:
                apt("ripgrep")


def install_exa():
    match distro:
        case "a":
            pacman("exa")
        case _:
            if distro == "d" or (distro == "u" and version >= 20.10):
                apt("exa")
            else:
                cargo("exa")
    logging.info("exa installed")


def install_yazi():
    match distro:
        case "a":
            pacman("yazi", "ffmpegthumbnailer", "unarchiver", "jq", "poppler")
        case _:
            if not exists("cargo"):
                install_cargo()
            cargo("yazi-fm")
    logging.info("yazi installed")


def install_all():
    install_fish()
    install_mylist(my_install_list)
    install_mcfly()
    install_starship()
    install_exa()
    config()
    install_cron()
    install_caddy()
    install_trojan_go()
    install_hysteria()
    install_fd()
    install_sd()
    install_rg()
    logging.info("all packages have installed")
