#!/usr/bin/env bash
#
# My linux init script loader.
#
# https://github.com/lxl66566/init-script
#
# This script is now only work for Archlinux, Debian and Ubuntu.

_red() {
    printf '\033[0;31;31m%b\033[0m' "$1"
}

error_exit()
{
    _red "Error: $1"
    exit 1
}

get_opsy() {
    [ -f /etc/redhat-release ] && awk '{print $0}' /etc/redhat-release && return
    [ -f /etc/os-release ] && awk -F'[= "]' '/PRETTY_NAME/{print $3,$4,$5}' /etc/os-release && return
    [ -f /etc/lsb-release ] && awk -F'[="]+' '/DESCRIPTION/{print $2}' /etc/lsb-release && return
}

NAME=$(get_opsy)
case "$NAME" in
    "Arch Linux*" )
        yes | pacman -Syu --needed git python || error_exit "安装所需依赖出错"
    ;;
    "Debian*" | "Ubuntu*" )
        apt update && apt install git python3 || error_exit "安装所需依赖出错"
    ;;
    *)
        printf "发行版不受支持"
        exit 1
    ;;
esac

# 实在不知道要放哪边还不会有权限问题，因此出此下策，放根目录

mypath="/absx"

mkdir -p $mypath || error_exit "创建目录失败"
cd $mypath
git clone https://github.com/lxl66566/init-script.git || error_exit "git clone 失败"
chmod 777 $mypath -R
cd init-script
python init.py $mypath
