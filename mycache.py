# cache utils
import contextlib
import functools
import logging
import pathlib
import pickle

from utils import colored, mypath


class mycache:
    """
    缓存系统
    """

    def __init__(self, name: str) -> None:
        self.cache_dir().mkdir(mode=0o777, exist_ok=True)
        self.file = self.cache_dir() / name

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

    @staticmethod
    def cache_dir() -> pathlib.Path:
        return (mypath() / ".cache").resolve()

    @staticmethod
    def simple_save(name: str) -> None:
        """
        set a bool value to True quickly
        """
        (mycache.cache_dir() / name).touch(0o777, exist_ok=True)

    @staticmethod
    def simple_load(name: str) -> bool:
        """
        load a bool value quickly
        """
        return (mycache.cache_dir() / name).exists()

    @staticmethod
    def simple_remove(name: str) -> bool:
        """
        set a bool value to False quickly
        """
        return (mycache.cache_dir() / name).unlink(missing_ok=True)


def mycache_once(name: str):
    """
    It's a decorator to record a function into disk cache, so it would exec only once.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if mycache(name).in_set(func.__name__):
                logging.warning(
                    f"{colored(func.__name__, 'green')} has previously been executed, so it won't be executed this time. If you wish to execute it regardless, please delete the cache file in {mycache.cache_dir() / name}."
                )
                return
            result = func(*args, **kwargs)
            mycache(name).append_set(func.__name__)
            return result

        return wrapper

    return decorator
