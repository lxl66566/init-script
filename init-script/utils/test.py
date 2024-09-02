class EnableTest:
    def __init__(self, test: bool = False):
        self.test = test

    def is_test(self) -> bool:
        return self.test
