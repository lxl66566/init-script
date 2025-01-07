#!/bin/bash

enable_bbr() {
    # 检查内核版本是否支持 BBR
    kernel_version=$(uname -r)
    if [[ ! "$kernel_version" =~ ^4\.[9-9]\.|^4\.[1-9][0-9]\.|^[5-9]\.|^[1-9][0-9] ]]; then
        echo "BBR is not supported in this kernel version ($kernel_version)."
        return 1
    fi
    
    # 检查是否支持 sysctl
    if ! command -v sysctl &> /dev/null; then
        echo "sysctl command is not supported on this system."
        return 1
    fi
    
    # 检查是否已经启用 BBR
    if sysctl net.ipv4.tcp_congestion_control | grep -q "bbr"; then
        echo "BBR is already enabled."
        return 0
    fi
    
    # 检查系统是否支持 BBR
    if ! lsmod | grep -q "bbr"; then
        echo "BBR module is not loaded. Attempting to load it..."
        modprobe tcp_bbr
        if [ $? -ne 0 ]; then
            echo "Failed to load BBR module. BBR might not be supported on this system."
            return 1
        fi
    fi
    
    # 启用 BBR
    echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
    echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
    
    # 应用新的配置
    sysctl -p
    
    # 再次检查是否成功启用 BBR
    if sysctl net.ipv4.tcp_congestion_control | grep -q "bbr"; then
        echo "BBR has been successfully enabled."
        return 0
    else
        echo "Failed to enable BBR."
        return 1
    fi
}

# 执行函数
enable_bbr
