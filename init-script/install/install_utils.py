import functools
import logging as log
import shlex
import subprocess

from ..utils import colored, pm, pm_fullname
from ..utils.mycache import mycache


def check_package_exists(package_name):
    if pm() == "p":
        command = f"pacman -Ss {package_name}"
    elif pm() == "a":
        command = f"apt-cache search {package_name}"
    elif pm() == "y":
        command = f"yum list {package_name}"
    elif pm() == "d":
        command = f"dnf list {package_name}"
    else:
        log.debug(f"Unsupported package manager: {pm_fullname()}")
        return False

    try:
        output = subprocess.check_output(shlex.split(command), stderr=subprocess.STDOUT)
        if output:
            log.debug(f"Package {package_name} exists in {pm_fullname()} repository.")
            return True
        else:
            log.debug(
                f"Package {package_name} does not exist in {pm_fullname()} repository."
            )
            return False
    except subprocess.CalledProcessError as e:
        log.debug(f"Error occurred while checking for package: {e.output}")
        return False


def install_once(name: str):
    """
    为 Package 类定制的成员函数装饰器，使每个包的 install 只会执行一次。
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            func_fullname = self.name
            if mycache(name).in_set(func_fullname):
                log.warning(
                    f"{colored(func_fullname, 'green')} has previously been executed, so it won't be executed this time. If you wish to execute it regardless, please delete the cache file in {mycache.cache_dir() / name}."
                )
                return
            result = func(self, *args, **kwargs)
            mycache(name).append_set(func_fullname)
            return result

        return wrapper

    return decorator


import unittest  # noqa: E402


class Test(unittest.TestCase):
    def test_check_package_exists(self):
        self.assertTrue(check_package_exists("sudo"))
        self.assertFalse(check_package_exists("jklasjfjklasdhf"))


if __name__ == "__main__":
    unittest.main()
