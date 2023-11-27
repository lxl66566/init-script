#!/usr/bin/env bash

_red() {
    printf '\033[0;31;31m%b\033[0m' "$1"
}
function error_exit()
{
    _red "Error: $1"
    exit 1
}

git add -A
git commit -m $(date "+%Y%m%d-%H:%M:%S")
git push origin py || error_exit "push failed"