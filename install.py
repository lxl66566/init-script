import logging
from pathlib import Path
from subprocess import run

from utils import *

# 多发行版通用的安装列表
my_install_list = [
    "sudo",
    "wget",
    "curl",
    "rsync",
    "make",
    "btop",
    "lsof",
    "zoxide",
    "fzf",
    "ncdu",
    "tldr",
    "trojan",
    "podman",
    "unzip",
]


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


def y_or_qy() -> str:
    """
    do you need quit mode?
    """
    if debug_mode():
        return "-y"
    else:
        return "-qy"


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
                "install",
                y_or_qy(),
                *args,
            )
        )
    )


def basic_install(*args):
    """
    basically install any packages by pm
    """
    cut()
    logging.info("开始安装：" + " ".join(args))
    match pm():
        case "p":
            pacman(*args)
        case _:
            day(*args)
    logging.info("安装完成：" + " ".join(args))


def cargo(*args):
    if exists("cargo"):
        rc_sudo(" ".join(("cargo install --locked", *args)))
    else:
        install_cargo()


def config_fish():
    if not (Path(mypath()) / "dotfile").exists():
        rc(
            "git clone https://github.com/lxl66566/dotfile.git -b archlinux --depth 1",
            cwd=mypath(),
        )
    dotfile = mypath().rstrip("/") + "/dotfile"
    rc(f"cp -rf {dotfile}/home/absolutex/.config/fish ~/fish", cwd=mypath())
    logging.info("copy fish config success")


# because AUR has a lot of problems, i decide to install them manually instead of AUR
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
    logging.info("install paru success")


def install_cron():
    match pm():
        case "p":
            pacman("cronie")
            rc_sudo("systemctl enable --now cronie")
        case _:
            basic_install("cron")
            rc_sudo("systemctl enable --now cron")


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
                        y_or_qy(),
                    )
                )
            )


def install_python_requests():
    match pm():
        case "p":
            basic_install("python-requests")
        case _:
            basic_install("python3-requests")


def install_gh_release(s: str):
    # TODO: complete this
    from mypy import *

    response = requests.get(
        "https://api.github.com/repos/eza-community/eza/releases/latest"
    )
    n = lambda s: s.rpartition("/")[-1].lower()
    dl_links = mylist(
        [i.get("browser_download_url") for i in response.json().get("assets")]
    )
    temp = (
        dl_links.filter(lambda x: "linux" in n(x))
        .filter(lambda x: "x86_64" in n(x) or "amd64" in n(x))
        .sort_by(lambda x, y: "musl" in n(x) and "musl" not in n(y))
    )


def install_trojan_go():
    assert exists("unzip"), "unzip not found"
    rc(
        "wget https://github.com/p4gefau1t/trojan-go/releases/latest/download/trojan-go-linux-amd64.zip",
        cwd="/tmp",
    )
    rc("unzip trojan-go-linux-amd64.zip -d /tmp/trojan-go", cwd="/tmp")
    rc_sudo("install -Dm 755 '/tmp/trojan-go/trojan-go' '/usr/bin/trojan-go'")
    rc_sudo(
        "install -Dm 644 '/tmp/trojan-go/ezample/trojan-go.service' '/usr/lib/systemd/system/trojan-go.service'"
    )
    rc_sudo(
        "install -Dm 644 '/tmp/trojan-go/ezample/trojan-go@.service' '/usr/lib/systemd/system/trojan-go@.service'"
    )
    rc("mkdir -p /etc/trojan-go")
    logging.info("install trojan-go success")


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
    logging.info("install caddy success")


def install_hysteria():
    rc_sudo("curl -fsSL https://get.hy2.sh/ | bash")
    logging.info("install hysteria success")


def install_fd():
    match pm():
        case "p":
            pacman("fd")
        case "a":
            ver = "8.7.1"
            name = f"fd-v{ver}-x86_64-unknown-linux-musl"
            rc(
                f"wget https://github.com/sharkdp/fd/releases/download/v{ver}/{name}.tar.gz",
                cwd="/tmp",
            )
            rc(
                f"tar -xvaf /tmp/{name}.tar.gz",
                cwd="/tmp",
            )
            rc_sudo(f"install -Dm755 '/tmp/{name}/fd' '/usr/bin/fd'")
            rc_sudo(
                f"install -Dm644 '/tmp/{name}/autocomplete/fd.fish' '/usr/share/fish/vendor_completions.d/fd.fish'"
            )
    logging.info("fd success installed")


def install_mcfly():
    match distro():
        case "a":
            pacman("mcfly")
        case _:
            rc_sudo(
                "curl -LSfs https://raw.githubusercontent.com/cantino/mcfly/master/ci/install.sh | sh -s -- --git cantino/mcfly"
            )
    logging.info("install mcfly success")


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
    logging.info("install zoxide success")


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
    logging.info("fish installed")


def install_starship():
    match distro():
        case "a":
            pacman("starship")
        case _:
            rc_sudo("curl -sS https://starship.rs/install.sh | sh -s -- -y")
    logging.info("starship installed")


def install_cargo():
    if exists("cargo"):
        return
    basic_install("cargo")
    # match distro():
    #     case "a":
    #         pacman("cargo")
    #     case _:
    #         rc_sudo("curl https://sh.rustup.rs -sSf | sh -s -- -y")
    logging.info("cargo installed")


def install_sd():
    sd_version = "1.0.0"
    sd_name = f"sd-v{sd_version}-x86_64-unknown-linux-musl"
    match pm():
        case "p":
            pacman("sd")
        case "a":
            if (distro() == "d" and version() < 13) or distro() == "u":
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
                basic_install("rust-sd")
    logging.info("sd installed")


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
    logging.info("rg installed")


def install_eza():
    match pm():
        case "p":
            pacman("eza")
        case _:
            name = "eza_x86_64-unknown-linux-musl"
            rc(
                f"wget https://github.com/eza-community/eza/releases/latest/download/{name}.tar.gz",
                cwd="/tmp",
            )
            rc(
                f"tar -xvaf /tmp/{name}.tar.gz",
                cwd="/tmp",
            )
            rc_sudo("install -Dm755 /tmp/eza /usr/bin/eza")

    logging.info("eza installed")


def install_yazi():
    match distro():
        case "a":
            pacman("yazi", "ffmpegthumbnailer", "unarchiver", "jq", "poppler")
        case _:
            # cargo("yazi-fm")
            yazi_name = "yazi-x86_64-unknown-linux-gnu"
            rc(
                f"wget https://github.com/sxyazi/yazi/releases/download/v0.1.5/{yazi_name}.zip",
                cwd="/tmp",
            )
            rc(
                f"unzip /tmp/{yazi_name}.zip",
                cwd="/tmp",
            )
            rc_sudo(f"install -Dm755 '/tmp/{yazi_name}/yazi' '/usr/bin/yazi'")
            rc_sudo(
                f"install -Dm644 '/tmp/{yazi_name}/completions/yazi.fish' '/usr/share/fish/vendor_completions.d/yazi.fish'"
            )
    logging.info("yazi installed")


def install_neovim():
    match distro():
        case "a":
            pacman("neovim")
        case _:
            name = "nvim-linux64"
            rc(
                f"wget https://github.com/neovim/neovim/releases/download/stable/{name}.tar.gz",
                cwd="/tmp",
            )
            rc(
                f"tar -xvaf /tmp/{name}.tar.gz",
                cwd="/tmp",
            )
            rc_sudo(f"install -Dm755 '/tmp/{name}/bin/nvim' '/usr/bin/nvim'")
            rc_sudo(
                """find . -type f -exec install -Dvm755 "{}" "/usr/{}" \;""",
                cwd=f"/tmp/{name}",
            )
    logging.info("neovim installed")


def install_fastfetch():
    match pm():
        case "p":
            pacman("fastfetch")
        case _:
            ver = "2.3.4"
            name = f"fastfetch-{ver}-Linux"
            rc(
                f"wget https://github.com/fastfetch-cli/fastfetch/releases/latest/download/{name}.tar.gz",
                cwd="/tmp",
            )
            rc(
                f"tar -xvaf /tmp/{name}.tar.gz",
                cwd="/tmp",
            )
            rc_sudo(
                """find usr -type f -exec install -Dvm755 "{}" "/{}" \;""",
                cwd=f"/tmp/{name}",
            )
    logging.info("fastfetch installed")


others = {
    "fish": install_fish,
    "base": install_base,
    "mcfly": install_mcfly,
    "starship": install_starship,
    "eza": install_eza,
    "my_config_option": config_fish,
    "cron": install_cron,
    "caddy": install_caddy,
    "trojan-go": install_trojan_go,
    "hysteria": install_hysteria,
    "fd": install_fd,
    "sd": install_sd,
    "rg": install_rg,
    "yazi": install_yazi,
    "neovim": install_neovim,
    "fastfetch": install_fastfetch,
}


def install_all():
    cut()
    logging.info(colored("starting to install ALL", "green"))
    basic_install(*my_install_list)

    for p in others.values():
        p()

    cut()
    logging.info("all packages have been installed")


def install_one(p: str):
    if p in my_install_list:
        basic_install(p)
        return
    try:
        others.get(p)()
    except TypeError:
        error_exit("脚本未收录此软件")
