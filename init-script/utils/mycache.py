import contextlib
import pathlib
import pickle
import shutil
import tempfile
import unittest
from typing import Any, Optional

from .test import EnableTest


def cache_dir() -> pathlib.Path:
    """
    return the cache directory
    """
    from ..utils import mypath

    return (mypath() / ".cache").resolve()


class TestCache(EnableTest):
    def __init__(self, test=False):
        super().__init__(test)
        if not self.is_test():
            self._cache_dir = cache_dir()
        else:
            # https://github.com/python/cpython/issues/100131 is a way to solve that, but it's too new
            # and cannot run on old python version
            self._cache_dir = pathlib.Path(tempfile.mkdtemp())

    def cache_dir(self) -> pathlib.Path:
        """
        return the cache directory
        """
        return self._cache_dir


class BaseCache(TestCache):
    """
    cache any object
    """

    def __init__(self, name: str, test=False) -> None:
        super().__init__(test)
        self.cache_dir().mkdir(mode=0o777, exist_ok=True)
        self.file = self.cache_dir() / name

    def load(self) -> Optional[Any]:
        """
        load data
        """
        if not self.file.exists():
            return None
        with self.file.open("rb") as f:
            return pickle.load(f)

    def save(self, data: Any) -> None:
        """
        save data
        """
        with self.file.open("wb") as f:
            pickle.dump(data, f)

    def clear(self) -> None:
        """
        clear cache
        """
        if self.file.exists():
            self.file.unlink()


class SetCache(BaseCache):
    """
    a set cache
    """

    def __init__(self, name: str) -> None:
        super().__init__(name)

    def in_set(self, data: Any) -> bool:
        """
        returns True if data in cache, False if data not in cache
        """
        if temp := self.load():
            assert isinstance(temp, set), "cannot use in_set to a non-set"
            return data in temp
        else:
            return False

    def append_set(self, data: Any) -> bool:
        """
        returns True if data actually added to cache, False if data has already in the cache
        """
        temp = self.load() or set()
        assert isinstance(temp, set), "cannot use append to a non-set"
        if data in temp:
            return False
        temp.add(data)
        self.save(temp)
        return True

    def remove_set(self, data: Any):
        """
        remove a value from cache set
        """
        temp = self.load()
        if not temp:
            return
        assert isinstance(temp, set), "cannot use remove to a non-set"
        with contextlib.suppress(KeyError):
            temp.remove(data)
        self.save(temp)


class SimpleCache:
    """
    a simple 01 cache, only cache a bool value
    """

    @staticmethod
    def cache_dir() -> pathlib.Path:
        return TestCache(True).cache_dir()

    @staticmethod
    def save(name: str) -> None:
        """
        set a bool value to True quickly
        """
        (SimpleCache.cache_dir() / name).touch(0o777, exist_ok=True)

    @staticmethod
    def load(name: str) -> bool:
        """
        load a bool value quickly
        """
        return (SimpleCache.cache_dir() / name).exists()

    @staticmethod
    def remove(name: str) -> None:
        """
        set a bool value to False quickly
        """
        (SimpleCache.cache_dir() / name).unlink(missing_ok=True)


class Test(unittest.TestCase):
    def test_base_cache(self):
        BaseCache("base1")
        data = {"test": 1, "test2": 2}
        BaseCache("base1").save(data)
        self.assertEqual(BaseCache("base1").load()["test"], 1)  # type: ignore
        self.assertEqual(BaseCache("base1").load()["test2"], 2)  # type: ignore
        BaseCache("base1").clear()
        self.assertIsNone(BaseCache("base1").load())

    def test_simple_cache(self):
        self.assertFalse(SimpleCache.load("simple"))
        SimpleCache.save("simple")
        self.assertTrue(SimpleCache.load("simple"))
        SimpleCache.save("simple")
        self.assertTrue(SimpleCache.load("simple"))
        SimpleCache.remove("simple")
        self.assertFalse(SimpleCache.load("simple"))

    def test_set_cache(self):
        self.assertFalse(SetCache("set").in_set("123"))
        self.assertTrue(SetCache("set").append_set("123"))
        self.assertTrue(SetCache("set").in_set("123"))
        self.assertFalse(SetCache("set").in_set("456"))
        self.assertFalse(SetCache("set").append_set("123"))
        self.assertTrue(SetCache("set").append_set("456"))
        self.assertTrue(SetCache("set").in_set("456"))
        # 123, 456
        SetCache("set").remove_set("123")
        self.assertFalse(SetCache("set").in_set("123"))
        self.assertTrue(SetCache("set").in_set("456"))


if __name__ == "__main__":
    unittest.main()
    shutil.rmtree(TestCache(True).cache_dir())
