from functools import reduce


class UFCS:
    """
    A simple [Uniform Function Call Syntax (UFCS)](https://tour.dlang.org/tour/en/gems/uniform-function-call-syntax-ufcs) implemention in python.

    Example:
    ```
    UFCS([1, 2, 1]).sorted(key=lambda x: x <= 1).map(lambda x: x * 2).print()
    ```
    """

    def __init__(self, val) -> None:
        self._val = val if not isinstance(val, UFCS) else val._val

    def filter(self, func):
        return UFCS((type(self._val))(filter(func, self._val)))

    def map(self, func):
        return UFCS((type(self._val))(map(func, self._val)))

    def reduce(self, func, start=None):
        return reduce(func, self._val, start)

    def __getattr__(self, __name: str) -> any:
        __call = getattr(globals().get("__builtins__"), __name, None)
        if __call:
            return lambda *args, **kwds: UFCS(__call(self._val, *args, **kwds))
        else:
            return lambda *args, **kwds: getattr(self._val, __name)(*args, **kwds)

    def __repr__(self) -> str:
        return repr(self._val)

    def __str__(self) -> str:
        return str(self._val)

    def __getitem__(self, index) -> any:
        return self._val[index]

    def __iter__(self):
        return iter(self._val)

    def __len__(self) -> int:
        return len(self._val)


# test
if __name__ == "__main__":
    UFCS([1, 2, 3]).map(lambda x: x * 2).filter(lambda x: x > 3).sorted().print()
    temp = UFCS([1, 2, 3])
    temp.append(5)
    temp.print()
    a = temp.reduce(lambda x, y: x + y, 10)
    print(a)
