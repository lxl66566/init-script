import logging as log
import shutil
import tempfile
import unittest
from pathlib import Path

from . import rc


def add_linux_conf(file_path: Path | str, **kwargs):
    """
    Add or update configuration settings in a Linux configuration file.

    Args:
        file_path (Path | str): The path to the configuration file.
        **kwargs: Key-value pairs representing the configuration settings to be added or updated.

    Returns:
        None

    Raises:
        FileNotFoundError: If the specified configuration file does not exist.

    Notes:
        - The function creates a backup of the original configuration file before making any changes.
        - The function updates the configuration file in-place.
        - Only non-comment lines starting with a valid configuration key are considered for updates.
        - If a configuration key is already present in the file, its value is updated.
        - If a configuration key is not present in the file, a new line is added for it.

    Example:
        add_linux_conf("/etc/myconfig.conf", key1="value1", key2="value2")
    """
    file_path = Path(file_path)
    bak_path = Path(tempfile.gettempdir()) / file_path.name
    shutil.copyfile(file_path, bak_path)

    lines = file_path.read_text().splitlines()
    while not lines[-1]:
        lines.pop()

    for index, line in enumerate(lines):
        if not line.strip() or line.startswith("#"):
            continue
        config_key = line.strip().partition("=")
        if config_key[1] != "=":
            continue
        config_key = config_key[0]

        # find matches
        key = config_key.strip()
        value = kwargs.get(key)
        if value is None:
            continue

        lines[index] = f"{key}={str(kwargs[key])}"
        kwargs[key] = None

    for key, value in kwargs.items():
        if value is None:
            continue
        lines.append(f"{key}={str(value)}")

    lines.append("")
    file_path.write_text("\n".join(lines))

    log.info(f"已更新配置文件：{file_path}，diff：")
    rc(f"diff {bak_path} {file_path} --color='auto'", capture_output=False, check=False)


class TestConf(unittest.TestCase):
    def test_conf(self):
        tmpdir = Path(tempfile.gettempdir()) / "test_conf"
        tmpdir.mkdir(parents=True, exist_ok=True)
        config_file = tmpdir / "config"
        config_file.write_text(
            """test1=1
test2=2
test3=3
"""
        )
        add_linux_conf(config_file, test4="4", test2=5)
        new_content = config_file.read_text()
        self.assertEqual(new_content.count("test2="), 1)
        self.assertIn("test2=5", new_content)
        self.assertIn("test4=4", new_content)

    def test_multi_write(self):
        tmpdir = Path(tempfile.gettempdir()) / "test_conf"
        tmpdir.mkdir(parents=True, exist_ok=True)
        config_file = tmpdir / "config"
        config_file.write_text(
            """test1=1
test2=2
"""
        )
        add_linux_conf(config_file, test1="111")
        add_linux_conf(config_file, test1="222")
        add_linux_conf(config_file, test1="333")
        add_linux_conf(config_file, test1="444")
        new_content = config_file.read_text()
        self.assertEqual(new_content.count("test1="), 1)
        self.assertIn("test1=444", new_content)


if __name__ == "__main__":
    unittest.main()
