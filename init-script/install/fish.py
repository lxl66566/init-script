# ruff: noqa: E402
import logging as log
from pathlib import Path

from ..utils import mypath, quiet, rc, rc_sudo
from ..var import FISH_CONFIG_FILE_PATH


def install_fish_on_debian():
    url = "https://download.opensuse.org/repositories/shells:/fish:/nightly:/master/Debian_10/amd64/"
    package_name = rc(
        f"""curl {url} | grep -Po "fish_3\..*?\.deb?" | tail -1""",
        capture_output=True,
        text=True,
    ).stdout.strip()
    rc(f"wget {url}{package_name}", cwd="/tmp")
    rc_sudo("dpkg -i " + package_name, cwd="/tmp")


def _remove_init(config_path: Path = FISH_CONFIG_FILE_PATH):
    """
    remove the init command in fish config file, because if the composit is not installed, the init command will cause error.
    """
    if not config_path.exists():
        log.warning("fish config file not found")
        return
    content = config_path.read_text(encoding="utf-8")
    content = "\n".join(
        filter(lambda x: not ("init fish" in x and "source" in x), content.split("\n"))
    )
    config_path.write_text(content, encoding="utf-8")


def post_install_fish():
    rc_sudo("chsh -s /usr/bin/fish")
    dotfile = mypath() / "dotfile"
    branch = "archlinux"
    if not dotfile.exists():
        rc(
            f"git clone https://github.com/lxl66566/dotfile.git -b {branch} --depth 1",
            cwd=mypath(),
        )
    else:
        rc(f"git fetch --all {quiet()} -f", cwd=dotfile)
        rc(f"git reset --hard origin/{branch}", cwd=dotfile)
    rc(
        f"cp -rf {(dotfile / 'home/absolutex/.config/fish').absolute()} {Path.home() / '.config'}",
        cwd=mypath(),
    )
    _remove_init()


def fish_add_config(config: str, config_path=FISH_CONFIG_FILE_PATH):
    """
    add a command into fish config file.
    """
    content = config_path.read_text(encoding="utf-8")
    string_to_add = [config.strip()]
    if not content.endswith("\n"):
        string_to_add.insert(0, "\n")
    string_to_add.append("\n")
    config_path.write_text(content + "".join(string_to_add), encoding="utf-8")


import unittest
from tempfile import TemporaryDirectory


class TestFish(unittest.TestCase):
    def test_fish_add_config(self):
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            config_file = tmpdir / "config.fish"
            config_file.write_text(
                """It's a test.
zoxide init fish|source  
save""",
                encoding="utf-8",
            )
            _remove_init(config_path=config_file)
            fish_add_config("test1", config_file)
            fish_add_config("test2", config_file)
            fish_add_config("test3", config_file)
            self.assertEqual(
                config_file.read_text(encoding="utf-8").strip(),
                """It's a test.
save
test1
test2
test3""",
                msg="test_fish_add_config failed",
            )


# This unittest should be run on vps, not local machine. (your local mechine may not has `/absx/.cache`)
if __name__ == "__main__":
    unittest.main()
