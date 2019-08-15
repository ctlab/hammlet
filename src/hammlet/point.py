__all__ = ["Point"]


class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @property
    def xy(self):
        return (self.x, self.y)

    def __eq__(self, other):
        return self.xy == other.xy

    def __add__(self, other):
        return self.__class__(self.x + other.x, self.y + other.y)

    def __neg__(self):
        return self.__class__(-self.x, -self.y)

    def __mul__(self, other):
        return self.__class__(self.x * other, self.y * other)
