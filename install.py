import logging
from subprocess import run

from utils import *

mypath = ""
distro = ""
version = ""

# 多发行版通用的安装列表
my_install_list = [
    "sudo",
    "wget",
    "curl",
    "btop",
    "fish",
    "zoxide",
    "fzf",
    "ncdu",
    "caddy",
    "trojan",
    "podman",
]


def init(main_path, distro_name, version_name):
    global mypath, distro, version
    mypath = main_path
    distro = distro_name
    version = version_name
    match distro:
        case "a":
            rc_sudo("pacman -Syu --noconfirm")
            rc_sudo("pacman -S --noconfirm archlinux-keyring")
            rc_sudo("pacman -S --needed --noconfirm base-devel")
        case "d" | "u":
            assert is_root(), "You need to be root to install packages."
            rc("apt update -y")
            rc("apt upgrade -y")
            if version == "10":
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


def pacman(*args):
    rc_sudo(" ".join("pacman", "-S", "--needed", "--noconfirm", *args))


def paru(*args):
    assert not is_root(), "paru must be run as non-root user"
    rc(" ".join("yes | paru -S --needed", *args))


def apt(*args):
    rc_sudo(" ".join("apt", "install", "-y", *args))


def install_mylist():
    match distro:
        case "a":
            pacman(*my_install_list)
        case "d" | "u":
            apt(*my_install_list)
    logging.info("install mylist success: ")
    logging.info(" ".join(my_install_list))


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
    rc(
        "wget https://github.com/p4gefau1t/trojan-go/releases/latest/download/trojan-go-linux-amd64.zip",
        cwd="/tmp",
    )
    rc("unzip trojan-go-linux-amd64.zip -d /tmp/trojan-go", cwd="/tmp")
    rc_sudo("mv /tmp/trojan-go/trojan/go /usr/bin/")
    rc_sudo("chmod +x /usr/bin/trojan-go")
    rc_sudo(
        "cp /tmp/trojan-go/example/trojan-go.service /etc/systemd/system/trojan-go.service"
    )
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
    rc_sudo("curl https://get.hy2.sh/ | bash")
    logging.info("install hysteria success")


def install_all():
    install_mylist()
    install_cron()
    install_caddy()
    install_trojan_go()
    install_hysteria()
