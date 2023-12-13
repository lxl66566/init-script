from functools import cmp_to_key


class mylist(list):
    def filter(self, func):
        return mylist(filter(func, self))

    def map(self, func):
        return mylist(map(func, self))

    def sort(self, **kwargs):
        return mylist(sorted(self, **kwargs))

    def sort_by(self, func):
        return self.sort(key=cmp_to_key(func))
