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
	python3 init.py
	exit 0
fi

# 安装所需包
packages="git python3"
if command -v pacman &>/dev/null; then
	pacman -Syu --needed --noconfirm python git
elif command -v apt &>/dev/null; then
	apt update -y
	apt install -qy $packages
elif command -v yum &>/dev/null; then
	yum update -y
	yum install -qy $packages
elif command -v dnf &>/dev/null; then
	dnf update -y
	dnf install -qy $packages
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
python3 init.py
