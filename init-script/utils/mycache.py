import contextlib
import functools
import pathlib
import pickle
import shutil
import tempfile
import unittest
from typing import Any

TEST = False


@functools.lru_cache
def cache_dir() -> pathlib.Path:
    """
    return the cache directory
    """
    if not TEST:
        from ..utils import mypath

        return (mypath() / ".cache").resolve()
    else:
        return pathlib.Path(tempfile.TemporaryDirectory(delete=False).name)


class BaseCache:
    """
    cache any object
    """

    def __init__(self, name: str) -> None:
        cache_dir().mkdir(mode=0o777, exist_ok=True)
        self.file = cache_dir() / name

    def load(self):
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
    def save(name: str) -> None:
        """
        set a bool value to True quickly
        """
        (cache_dir() / name).touch(0o777, exist_ok=True)

    @staticmethod
    def load(name: str) -> bool:
        """
        load a bool value quickly
        """
        return (cache_dir() / name).exists()

    @staticmethod
    def remove(name: str) -> None:
        """
        set a bool value to False quickly
        """
        (cache_dir() / name).unlink(missing_ok=True)


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
    TEST = True
    unittest.main()
    shutil.rmtree(cache_dir())
    TEST = False
