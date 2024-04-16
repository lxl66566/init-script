import subprocess

from . import rc_sudo
from .mycache import SetCache

map_name_servicename = {
    "caddy": "caddy",
    "hysteria": "hysteria-server@hysteria",
    "trojan-go": "trojan-go",
    "trojan": "trojan",
    "openppp2": "openppp2",
}


def show_all_status():
    """
    展示服务运行状态
    """

    def show_one_status_and_restart_failed(service: str):
        rc_sudo(f"systemctl status {service} --no-pager", check=False)
        if is_service_running(service):
            rc_sudo(f"systemctl restart {service}", check=False)

    for name, service in map_name_servicename.items():
        if SetCache("package_installed").in_set(name):
            show_one_status_and_restart_failed(service)


def restart_all_services():
    """
    重启所有服务
    """
    for name, service in map_name_servicename.items():
        if SetCache("package_installed").in_set(name):
            rc_sudo(f"systemctl restart {service}", check=False)


def is_service_running(service_name: str):
    """
    检查服务是否正在运行
    :param service_name: 待检查的服务名
    :return: 如果服务正在运行返回 True，否则返回 False
    """
    cmd = ["systemctl", "is-active", service_name]
    output = subprocess.check_output(cmd).decode().strip()
    return output == "active"
