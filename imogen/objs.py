from __future__ import annotations
import typing as t
from dataclasses import dataclass
from PIL import ImageColor


@dataclass
class Point:
    x: int | DeferredOperation[int]
    y: int | DeferredOperation[int]

    # TODO: loop variables with expressions as a point dont seem to work?
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
class Color:
    r: int | DeferredOperation[int]
    g: int | DeferredOperation[int]
    b: int | DeferredOperation[int]
    a: int = 255

    def __str__(self):
        return f"rgba({self.r}, {self.g}, {self.b}, {self.a})"

    @property
    def as_tuple(self):
        return (self.r, self.g, self.b, self.a)

    @classmethod
    def from_str(cls, s):
        # if isinstance(items, list) and len(items) == 3:
        #     return ImageColor.getrgb("rgb(" + ",".join(map(str, items)) + ")")
        try:
            return ImageColor.getrgb(s)
        except ValueError:
            pass
        try:
            # Limit to 6 characters here
            return ImageColor.getrgb("#" + s)
        except ValueError:
            raise ValueError(f"Invalid color {s}")


@dataclass
class IMImage:
    name: str
    size: Point | DeferredOperation[Point]
    color: str
    text: str
    # piped : bool = False


@dataclass
class IntermediateImage:
    offset: Point | DeferredOperation[Point]
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
    piped: bool = False


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

    @staticmethod
    def Eval(arg, ctx):
        if arg is None:
            # In case you're evaluating left and right and one is None.
            return arg
        # breakpoint()
        if isinstance(arg, DeferredOperation):
            newval = arg.evaluate(ctx)
            return DeferredOperation.Eval(newval, ctx)
        elif isinstance(arg, Point):
            p = Point(
                DeferredOperation.Eval(arg.x, ctx), DeferredOperation.Eval(arg.y, ctx)
            )
            print(p)
            return p
        elif isinstance(arg, Color):
            c = Color(
                DeferredOperation.Eval(arg.r, ctx),
                DeferredOperation.Eval(arg.g, ctx),
                DeferredOperation.Eval(arg.b, ctx),
                DeferredOperation.Eval(arg.a, ctx),
            )
            print(c)
            return c
        elif type(arg) in [int, str, float, bool, tuple]:
            return arg
        elif isinstance(arg, FnCall):
            # Evlauate args?
            # breakpoint()
            return arg.eval()
        raise ValueError(f"Havent processed deferred type of {type(arg)} (value {arg})")

    # Something like this..
    def evaluate(self, context):
        # Check for the base cases before checking for
        # recursing on expressions
        if isinstance(self.left, LoopVar):
            # FOR LOOP VARS YOU CANNOT JUST SET SELF.LEFT TO THE VALUE
            # -- WE NEED TO RETAIN THE LOOPVAR OBJECT
            # SO THAT WE LOOK UP THE VALUE EACH TIME!
            left_value = context.vars.get(self.left.name).value
        elif isinstance(self.left, FnCall):
            left_value = self.left.eval()
        # MUST CHECK FN CALL AND ALL OTHER CHILDREN BEFORE THE PARENT DEFERRED
        # OPERATION
        elif isinstance(self.left, DeferredOperation):
            # Deferred Operations, though, should they be set?
            left_value = self.left.evaluate(context)
        else:
            left_value = self.left

        if isinstance(self.right, LoopVar):
            right_value = context.vars.get(self.right.name).value
        elif isinstance(self.right, FnCall):
            right_value = self.right.eval()
        elif isinstance(self.right, DeferredOperation):
            right_value = self.right.evaluate(context)
        else:
            right_value = self.right

        res = self.operation(left_value, right_value)
        print(self, "::", res)  # self.left, self.right, "=>", res)
        return res

    def __call__(self, *args):
        return DeferredOperation(self, args, lambda x, y: x(*y))

    # TODO: defer so that executing these values looks up the var value
    def __hash__(self):
        return hash(self.name)

    def __int__(self):
        return DeferredOperation(self, 0, lambda x, y: int(x))

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

    def __int__(self):
        return DeferredOperation(self, 0, lambda x, y: int(x))

    def __rmod__(self, other):
        return DeferredOperation(other, self, lambda x, y: x % y)


class LoopVar(DeferredOperation):
    # Make LoopVar a subclass of DeferredOperation
    # so that it gets all the operations defined on it.
    # Make self.left = self so that when DeferredOperation is evaluated,
    # it looks up the value of the loop var.
    # Make self.right empty because we don't ever need it,
    # and make self.operation the identify function,
    # as prior to calling it, the DefferedOperation.evaluate
    # will have already looked up the value of the loop var.
    def __init__(self, name):
        self.name = name
        self.left = self
        self.right = None
        self.operation = lambda x, _: x
        self.value = None


class FnCall(DeferredOperation):
    def __init__(self, fn_obj, args, deferred=False):
        # FN obj is a function object (python)stored in vars
        # So that FN Obj when parsing with operators and exprs
        # can benefit from the defined ops in DeferredOperation

        self.fn_obj = fn_obj
        self.args = list(filter(lambda x: x is not None, args))
        self.deferred = deferred

        if self.deferred:
            self.name = self.fn_obj.__name__
            self.left = self
            self.right = None
            self.operation = lambda x, _: x.eval()  # self.eval()
            self.value = None

    def eval(self):
        # This shouldn't be called unless we're unpacking something deferred,
        # or are not defferred ourselves.
        # return self.fn_obj(*self.args)
        # Need to return deferred operations when we evaluate since we do that in the xformer
        # if self.deferred:
        #     self.deferred = False  # For evaluation
        #     return DeferredOperation(self.fn_obj, self.args, lambda x, y: x(*y))
        # # Check if any args are deferred Fn Calls
        # elif any(isinstance(arg, FnCall) and arg.deferred for arg in self.args):
        #     self.deferred = False
        #     # Promote this call to deferred
        #     return DeferredOperation(self.fn_obj, self.args, lambda x, y: x(*y))
        # if any(isinstance(arg, DeferredOperation) for arg in self.args):
        #     #     self.deferred = False
        #     return DeferredOperation(self.fn_obj, self.args, lambda x, y: x(*y))
        # else:
        args = [
            arg.Eval(arg, self) if isinstance(arg, DeferredOperation) else arg
            for arg in self.args
        ]
        if isinstance(self.fn_obj, DeferredOperation):
            fn = DeferredOperation.Eval(self.fn_obj, self)
        else:
            fn = self.fn_obj
        res = fn(*args)
        return res

        # Convert all args from deferred, as well as fn
        # to their actual values:
        pass
