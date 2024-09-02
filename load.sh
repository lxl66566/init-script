#!/usr/bin/env bash
#
# My linux init script loader.
#
# https://github.com/lxl66566/init-script
#
# This script is only work for Archlinux, Debian and Ubuntu.
#
# PLEASE RUN AS ROOT, YOU ARE AWARE OF THE RISKS INVOLVED AND CONTINUE.

_red() {
    printf '\033[0;31;31m%b\033[0m' "$1"
}

error_exit() {
    _red "Error: $1"
    exit 1
}

run_script() {
    python3 -m init-script "$@"
}


update_source(){
    # usage: update_source <cache_path> <command>
    
    # 检查是否提供了命令参数
    if [[ -z "$2" ]]; then
        echo "请提供要执行的命令作为第二个参数，例如：update_source log_command 'git fetch'"
        exit 1
    fi
    
    FETCH_LOG_FILE="$1/.git_fetch_time.log"
    current_time=$(date +%s)
    # 如果日志文件存在，读取上一次 fetch 的时间
    if [[ -f "$FETCH_LOG_FILE" ]]; then
        last_fetch_time=$(cat "$FETCH_LOG_FILE")
    else
        last_fetch_time=0  # 如果没有记录文件，假设上次 fetch 时间为 0（即很久以前）
    fi
    
    # 计算时间差（以秒为单位）
    time_diff=$((current_time - last_fetch_time))
    
    # 检查时间差是否小于一天（86400秒）
    if (( time_diff < 86400 )); then
        echo "距离上一次执行 `$2` 不到一天，跳过此次操作。"
        exit 0
    fi
    
    # 执行 command
    eval "$2"
    
    # 更新日志文件记录此次 fetch 的时间
    echo "$current_time" > "$FETCH_LOG_FILE"
    echo "`$2` 执行完成，时间已记录。"
}

default="/absx"
if [ -z "$mypath" ]; then
    export mypath=$default
fi
if [[ ! $mypath = /* ]]; then
    printf "环境变量不合格，使用默认安装主目录\n"
    export mypath=$default
fi
printf "安装主目录：$mypath\n"

lockfile=$mypath"/.lock_for_load" # 避免二次 clone 的问题
if [ -e $lockfile ]; then
    cd $mypath"/init-script"
    update_source $mypath "git fetch --all && git reset --hard origin/py"
    run_script
    exit 0
fi

# 安装所需包
packages="git python3"
if command -v pacman &>/dev/null; then
    pacman -Sy --noconfirm archlinux-keyring
    pacman -Syu --needed --noconfirm python git
    elif command -v apt &>/dev/null; then
    export DEBIAN_FRONTEND=noninteractive
    export NEEDRESTART_MODE=a
    apt update -y
    apt install -qy $packages
    elif command -v yum &>/dev/null; then
    yum update -y
    yum install -qy $packages
    elif command -v dnf &>/dev/null; then
    dnf update -y
    dnf install -qy $packages
fi

# 检查 Python 版本 (针对 debian 11)
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
python_minor_version=$(echo "$python_version" | cut -d '.' -f 2)
if [ "$python_minor_version" -lt 10 ]; then
    # 检查系统是否为 Debian
    if [ -f /etc/debian_version ]; then
        # 替换 sources.list 中的 "bullseye" 为 "bookworm"
        sed -i 's/bullseye/bookworm/g' /etc/apt/sources.list
        echo "Replaced 'bullseye' with 'bookworm' in /etc/apt/sources.list"
        apt update -y
        DEBIAN_FRONTEND=noninteractive apt --yes upgrade python3
    else
        echo "Your python version is not 3.10 or higher, and here's not a Debian system."
        echo "Please install Python 3.10 or higher and try again."
        exit 1
    fi
else
    echo "Python version is 3.10 or higher."
fi

# 实在不知道要放哪边还不会有权限问题，因此出此下策，放根目录

mkdir -p $mypath || error_exit "创建目录失败"
cd $mypath
git config --global --add safe.directory '*'
rm -rf init-script
git clone https://github.com/lxl66566/init-script.git --filter=tree:0 || error_exit "git clone 失败"
touch $lockfile
chmod 777 $mypath -R || error_exit "授权失败"
cd init-script
run_script
