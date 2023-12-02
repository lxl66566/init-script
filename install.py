from subprocess import run

from utils import *

mypath = ""
distro = ""
version = ""

# 多发行版通用的安装列表
my_install_list = ["wget", "btop", "fish", "zoxide", "fzf", "ncdu", "caddy", "trojan"]


def init(main_path, distro_name, version_name):
    global mypath, distro, version
    mypath = main_path
    distro = distro_name
    version = version_name
    match distro:
        case "a":
            rc("sudo pacman -Syu --noconfirm")
            rc("sudo pacman -S --noconfirm archlinux-keyring")
            rc("sudo pacman -S --needed --noconfirm base-devel")
        case "d" | "u":
            rc("sudo apt update -y")
            rc("sudo apt upgrade -y")


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
        case "d":
            apt(*my_install_list)


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


def install_cron():
    match distro:
        case "a":
            pacman("cronie")
            rc("sudo systemctl enable --now cronie")
        case "d" | "u":
            apt("cron")
            rc("systemctl enable --now cron")


def install_all():
    install_mylist()
    if distro == "a":
        install_paru()
    install_cron()
