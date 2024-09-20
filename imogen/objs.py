import typing as t
from dataclasses import dataclass


@dataclass
class Point:
    x: int
    y: int

    @property
    def as_tuple(self):
        return (self.x, self.y)

    def __add__(self, other):
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y)
        return Point(self.x + other, self.y + other)

    def __mul__(self, other):
        if isinstance(other, Point):
            return Point(self.x * other.x, self.y * other.y)
        return Point(self.x * other, self.y * other)


@dataclass
class IMImage:
    name: str
    size: Point
    color: str
    text: str
    # piped : bool = False


@dataclass
class IntermediateImage:
    offset: Point
    piped: bool
    image: IMImage


@dataclass
class Composition(IMImage):
    composition: list[IntermediateImage]
    # offset: Point = field(default_factory=lambda _: Point(0, 0))


@dataclass
class Local:
    obj: t.Union[IMImage, Composition]


@dataclass
class LocalVar(Local):
    varname: str


@dataclass
class Repeated:
    body: t.List[IntermediateImage]
    loop_var: t.Optional[str]
    count: t.Union[int, LocalVar]


@dataclass
class IntermediateRepeatedImage:
    repeated_offset: Point
    local_offset: Point
    image: IMImage


@dataclass
class DeferredOperation:
    left: t.Any
    right: t.Any
    operation: t.Callable[[t.Any, t.Any], t.Any]

    # Something like this..
    def evaluate(self, context):
        if isinstance(self.left, LoopVar):
            self.left = context.vars.get(self.left.name)
        if isinstance(self.right, LoopVar):
            self.right = context.vars.get(self.right.name)

        left_value = (
            self.left.evaluate(context)
            if isinstance(self.left, DeferredOperation)
            else self.left
        )
        right_value = (
            self.right.evaluate(context)
            if isinstance(self.right, DeferredOperation)
            else self.right
        )
        return self.operation(left_value, right_value)


@dataclass
class LoopVar:
    name: str  # Defer lookup until runtime.

    # TODO: defer so that executing these values looks up the var value
    def __hash__(self):
        return hash(self.name)

    def __add__(self, other):
        return DeferredOperation(self, other, lambda x, y: x + y)

    def __radd__(self, other):
        return DeferredOperation(other, self, lambda x, y: x + y)

    def __rmul__(self, other):
        return DeferredOperation(other, self, lambda x, y: x * y)

    def __sub__(self, other):
        return DeferredOperation(self, other, lambda x, y: x - y)

    def __mul__(self, other):
        return DeferredOperation(self, other, lambda x, y: x * y)

    def __truediv__(self, other):
        return DeferredOperation(self, other, lambda x, y: x / y)

    def __floordiv__(self, other):
        return DeferredOperation(self, other, lambda x, y: x // y)

    def __mod__(self, other):
        return DeferredOperation(self, other, lambda x, y: x % y)

    def __pow__(self, other):
        return DeferredOperation(self, other, lambda x, y: x**y)

    def __eq__(self, other):
        return DeferredOperation(self, other, lambda x, y: x == y)

    def __ne__(self, other):
        return DeferredOperation(self, other, lambda x, y: x != y)

    def __lt__(self, other):
        return DeferredOperation(self, other, lambda x, y: x < y)

    def __le__(self, other):
        return DeferredOperation(self, other, lambda x, y: x <= y)

    def __gt__(self, other):
        return DeferredOperation(self, other, lambda x, y: x > y)

    def __ge__(self, other):
        return DeferredOperation(self, other, lambda x, y: x >= y)

    def __as_int__(self):
        return DeferredOperation(self, 0, lambda x: int(x))
