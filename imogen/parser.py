from lark import Transformer, Lark
from PIL import ImageColor
from imogen.objs import (
    Composition,
    DeferredOperation,
    IMImage,
    IntermediateImage,
    Local,
    LocalVar,
    LoopVar,
    Point,
    Repeated,
)
from pathlib import Path

with open("C:/imogen/grammar.lark", "r") as fp:
    dsl_grammar = fp.read()

# TODO: clean up grammar so its not ambigous with NAME / value stuff for now
parser = Lark(dsl_grammar, start="start", parser="earley")


# https://stackoverflow.com/a/73014859
def flatten(arg):
    if not isinstance(arg, list):
        yield arg
    else:
        for sub in arg:
            yield from flatten(sub)


class ImageTransformer(Transformer):
    def __init__(self):
        self.vars = {}

    def start(self, items):
        return items

    def statement(self, items):
        return items[0]

    def expr(self, items):
        return items[0]

    def add(self, items):
        return items[0] + items[1]

    def sub(self, items):
        return items[0] - items[1]

    def mul(self, items):
        return items[0] * items[1]

    def mod(self, items):
        return items[0] % items[1]

    def intdiv(self, items):
        return items[0] // items[1]

    def div(self, items):
        return items[0] / items[1]

    def expr_attr(self, items):
        return getattr(items[0], items[1])

    def image_decl(self, items):
        _local, item = items
        if _local is None:
            return item
        return Local(item)

    def assgn_stmt(self, items):
        _, name, value = items
        v = LocalVar(value, name)
        self.vars[name] = v
        return v

    def NAME(self, items):
        return items.value

    def value(self, items):
        return items[0]

    def NAME_REF(self, items):
        if (val := self.vars.get(items)) is not None:
            if isinstance(val, LocalVar):
                return val.obj
            return val  # An IMAGE
        # raise ValueError(f"Variable {items} not found")
        self.vars[items.value] = None

    def INT(self, items):
        return int(items.value)

    def named_image_decl(self, items):
        name, image = items
        image.name = name
        self.vars[name] = image
        return image

    def composition_ref(self, items):
        return items[0]

    def image_spec_expr(self, items):
        size, color, text, composition_body = items
        # try:
        text = text.strip('"')
        # except:

        # breakpoint()
        if composition_body is not None:
            return Composition(None, size, color, text, composition_body)
        else:
            return IMImage(None, size, color, text)

    def size(self, items):
        # Floating points from calculations must be coerced to integer
        # when specified as size!
        if isinstance(items[0], float):
            raise ValueError("Size must be an integer")
        return Point(items[0], items[1])
        # if isinstance(items[0], LoopVar):
        #     # Defer it
        #     return Point(items[0], items[1])
        # return Point(int(items[0]), int(items[1]))

    def color(self, items):
        print(items)
        if isinstance(items, list) and len(items) == 3:
            return ImageColor.getrgb("rgb(" + ",".join(map(str, items)) + ")")
        try:
            return ImageColor.getrgb(items[0])
        except ValueError:
            pass
        try:
            # Limit to 6 characters here
            return ImageColor.getrgb("#" + items[0])
        except ValueError:
            raise ValueError(f"Invalid color {items}")

    def text(self, items):
        return items[0]

    def composition_body(self, items):
        # Flatten any piped lists, which are returned as a tuple since
        # we need to return something from them, right?
        # So we get some cursed stacking of lists here.
        # TODO: fix this cursed shit
        new = []
        for item in items:
            if isinstance(item, list):
                # TODO: flatten?
                new.extend(flatten(item))
            elif isinstance(item, LocalVar):
                # Transformer will already have visited and computed this.
                pass
            else:
                new.append(item)
        # breakpoint()
        return new

    def composition_ref_img(self, items):
        offset, image = items
        return IntermediateImage(offset, False, image)

    def composition_repeated_img(self, items) -> Repeated:
        # NO LOOP VARS IN REPEATED.
        offset, repeated = items
        components = []
        for r in repeated.body:
            if isinstance(r, Repeated):
                # Flatten out the repetitions with the added offsets, need the nesting.
                rs = self.composition_repeated_img((offset, r))
                components.append(rs)
            else:
                # breakpoint()
                r.offset += offset
                components.append(r)
        repeated.body = components
        return repeated

    def composition_ref_anon_img(self, items):
        offset, anonymous_image = items
        return IntermediateImage(offset, False, anonymous_image)

    def anonymous_image_expr(self, items):
        image = items[0]
        return image

    def piped_composition_ref(self, items):
        first, second = items
        # It will be an INTERMEDIATE IMAGE here always since we're in composition
        # TODO: fails if Repeated!
        # TODO who knows if itll work?
        second.piped = True
        return [first, second]

    def NUMBER(self, items):
        try:
            return int(items.value)
        except ValueError:
            return float(items.value)

    def loop_var(self, items):
        var = LoopVar(items[0])
        self.vars[var.name] = var  # Unassigned as of now.
        return var

    # Loop var needs to be assigned BEFORE we go into the body!
    def prepare_repeated(self, items):
        loop_var, count, body = items
        # This cannot possibly work because of the TRANSFORMER CALCULATING IT AS IT WALKS!
        # TODO
        return Repeated(body, loop_var, count)
