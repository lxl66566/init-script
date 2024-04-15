# cache utils
import contextlib
import pathlib
import pickle

from ..utils import mypath


def cache_dir() -> pathlib.Path:
    return (mypath() / ".cache").resolve()


class BaseCache:
    """
    cache any object
    """

    def __init__(self, name: str) -> None:
        cache_dir().mkdir(mode=0o777, exist_ok=True)
        self.file = cache_dir() / name

    def load(self) -> any:
        """
        load data
        """
        if not self.file.exists():
            return None
        with self.file.open("rb") as f:
            return pickle.load(f)

    def save(self, data: any) -> None:
        """
        save data
        """
        with self.file.open("wb") as f:
            pickle.dump(data, f)


class SetCache(BaseCache):
    """
    a set cache
    """

    def __init__(self, name: str) -> None:
        super().__init__(name)

    def in_set(self, data: any) -> bool:
        """
        returns True if data in cache, False if data not in cache
        """
        if temp := self.load():
            assert isinstance(temp, set), "cannot use in_set to a non-set"
            return data in temp
        else:
            return False

    def append_set(self, data: any) -> bool:
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

    def remove_set(self, data: any):
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
    def remove(name: str) -> bool:
        """
        set a bool value to False quickly
        """
        return (cache_dir() / name).unlink(missing_ok=True)
