#!/usr/bin/env bash
#
# My linux init script.
#
# https://github.com/lxl66566/init-script

set -euo pipefail
trap _exit INT QUIT TERM

_red() {
    printf '\033[0;31;31m%b\033[0m' "$1"
}

_green() {
    printf '\033[0;31;32m%b\033[0m' "$1"
}

_yellow() {
    printf '\033[0;31;33m%b\033[0m' "$1"
}

_blue() {
    printf '\033[0;31;36m%b\033[0m' "$1"
}

_exists() {
    local cmd="$1"
    if eval type type >/dev/null 2>&1; then
        eval type "$cmd" >/dev/null 2>&1
        elif command >/dev/null 2>&1; then
        command -v "$cmd" >/dev/null 2>&1
    else
        which "$cmd" >/dev/null 2>&1
    fi
    local rt=$?
    return ${rt}
}

_exit() {
    _red "\nThe script has been terminated."
    exit 1
}

next() {
    printf "%-70s\n" "-" | sed 's/\s/-/g'
}

get_opsy() {
    [ -f /etc/redhat-release ] && awk '{print $0}' /etc/redhat-release && return
    [ -f /etc/os-release ] && awk -F'[= "]' '/PRETTY_NAME/{print $3,$4,$5}' /etc/os-release && return
    [ -f /etc/lsb-release ] && awk -F'[="]+' '/DESCRIPTION/{print $2}' /etc/lsb-release && return
}

function error_exit()
{
    _red "Error: $1"
    exit 1
}

if [ $(uname) != "Linux" ]; then
    error_exit "脚本只能执行在（我用过的） Linux 系统上"
fi

# get system information
NAME=$(get_opsy)
AARCH=$(uname -m)
default_install=(git wget curl openssh)
my_install=(mcfly)
proxy_install=(trojan hysteria-bin trojan-go-bin)

# input an array of package name, output converted array
function map_pac_name() {
    local new_array=()
    for i in "$@"; do
        case "$i" in
            "*-bin" )
                new_array=("${new_array[@]}" "aur://$i")
            ;;
            *)
                new_array=$(new_array "$i")
            ;;
        esac
    done
    return ${new_array[@]}
}

# input an array and install all of them
function install_any() {
    case "$NAME" in
        "Arch Linux" )
            yes | sudo pacman -Syu --needed $(map_pac_name "$@") || error_exit "安装出错"
        ;;
        "Debian*" )
            sudo apt update && sudo apt install $@
        ;;
        *)
            printf "发行版不受支持"
            exit 1
        ;;
    esac
}


# install_any ${default_install[@]}
install_any ${my_install[@]}