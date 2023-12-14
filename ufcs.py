class UFCS:
    """
    Usage:
    ```
    UFCS([1, 2, 1]).sorted(key=lambda x: x <= 1).map(lambda x: x * 2).print()
    ```
    """

    def __init__(self, val) -> None:
        self._val = val if not isinstance(val, UFCS) else val._val

    def __getattr__(self, __name: str) -> any:
        __call = globals()["__builtins__"].get(__name)
        if __name in ("filter", "map"):
            return lambda *args: UFCS(type(self._val)(__call(*args, self._val)))
        else:
            return lambda *args, **kwds: UFCS(__call(self._val, *args, **kwds))

    def __str__(self) -> str:
        return str(self._val)

    def __getitem__(self, index) -> any:
        return self._val[index]


if __name__ == "__main__":
    UFCS(["1", "2"]).print()
