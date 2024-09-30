from PIL import Image, ImageDraw
from imogen.objs import (
    Composition,
    DeferredOperation,
    FnCall,
    IMImage,
    IntermediateImage,
    Local,
    LocalVar,
    LoopVar,
    Point,
    Repeated,
)

from copy import deepcopy


class Render:

    def evaluate(self, node):
        if isinstance(node, DeferredOperation):
            return node.evaluate(self)
        return node

    def __init__(self, tree, metadata):
        self.tree = tree
        self.metadata = metadata
        self.generated_images = {}

    @property
    def vars(self):
        return self.metadata["vars"]

    def create_image(self, image: IMImage) -> Image:
        # Recall you must evaluate the deferred operation
        # as close to its usage as possible, which would be here
        # YOU CANNOT OVERWRITE DEFFERED OPERATION VALUES THEMSELVES.
        # YOU NEED TO JUST GET A VALUE SIZE DIFFERENTLY!
        # TODO: ANY ACCESSES OF AN OBJECT (image.name, image.size, etc)
        # NEED TO BE ALWAYS ASSUMED TO BE DEFERRED OPERATIONS!
        # FOR EXAMPLE, THE TEXT COULD CHANGE EACH LOOP ITERATION TOO!
        size = DeferredOperation.Eval(image.size, self)
        text = str(
            DeferredOperation.Eval(image.text, self)
        )  # Have to convert for the PIL lib
        color = DeferredOperation.Eval(image.color, self)
        print(">>>>", color)
        if not isinstance(color, tuple):
            color = color.as_tuple
        print(f"Creating image {image.name} with size {size.x}, {size.y}")
        #        breakpoint()
        img = Image.new("RGB", (size.x, size.y), color)
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), text, fill=(0, 0, 0))
        return img

    def do_repeated(
        self, repeated: Repeated, img: Image, comp: Composition, top_left: Point
    ):
        top_left = DeferredOperation.Eval(top_left, self)
        if repeated.piped:
            top_left = Point(0, 0)
        # breakpoint()
        for i in range(repeated.count):
            # Generate all the images
            if repeated.loop_var:
                self.vars[repeated.loop_var].value = i
                print("INCREMENTING LOOP VAR", i)
            _rimg: IntermediateImage
            # CURSED:
            # GO ACCESS EVERY VARIABLE, STORE THE VALUE OF IT,
            # EVALUATE THE BODY, THEN RESTORE THE VALUE

            for _rimg in repeated.body:

                # HANDLE NESTING HERE
                if isinstance(_rimg, Repeated):
                    # BASICALLY WE ARE JUST PUSHING SCOPE HERE.
                    # TODO: STANDARDIZE OUTSIDE OF REPEATS.
                    previous_vars = deepcopy(self.vars)
                    for v in self.vars:
                        # Evaluate all the vars here
                        if isinstance(self.vars[v], LocalVar):
                            # Here we go from (possibly) deferred, to executed
                            self.vars[v].obj = DeferredOperation.Eval(
                                self.vars[v].obj, self
                            )
                        # Nothing to do for Loop vars, they get handled properly later.
                        elif isinstance(self.vars[v], LoopVar):
                            pass

                    top_left = self.do_repeated(_rimg, img, comp, top_left)
                    # Now restore it!
                    self.metadata["vars"] = previous_vars
                    continue

                piped = _rimg.piped
                # Already has the repeat global offset
                offset = DeferredOperation.Eval(_rimg.offset, self)
                _rimg_img: IMImage = _rimg.image
                size = DeferredOperation.Eval(_rimg_img.size, self)  # MUST EVAL IT HERE
                # breakpoint()
                _real_img = self.create_image(_rimg_img)
                if piped:
                    print("(rep) pipe")
                    paste_x = 0
                    paste_y = 0
                else:
                    paste_x = top_left.x + offset.x
                    paste_y = top_left.y + offset.y
                print(f"(rep) write to {paste_x}, {paste_y}")
                img.paste(
                    _real_img,
                    (
                        paste_x,
                        paste_y,
                        paste_x + size.x,
                        paste_y + size.y,
                    ),
                )
                top_left.x = paste_x + size.x
                if top_left.x >= comp.size.x:
                    top_left.x = 0
                    top_left.y += size.y
                    if top_left.y >= comp.size.y:
                        print("Composition size exceeded... doing nothing though")

        return top_left

    # Write code that will take a Composition object and create a PIL image
    # REPEATED THINGS ARE NOT RELATIVE -- THEY ARE NOT SCOPED! THEY ARE SCOPED TO THE PARENT COMPOSITION!
    # FOR SCOPING, USE COMPOSITIONS!
    def create_composition(self, composition: Composition) -> Image:
        size = DeferredOperation.Eval(composition.size, self)
        color = DeferredOperation.Eval(composition.color, self)
        img = Image.new("RGB", (size.x, size.y), color)
        top_left = Point(0, 0)

        # Insert repeated image code into the middle of the composition list where it appears

        # TODO: Extend the composition images with the body of the repeater,
        # but also track which instruction is a repeat; keep a stack of repeats,
        # and increment loop variables awccordingly. Need to flatten this
        # so that pipes work?

        for intermediate in composition.composition:
            intermediate_image = None
            if isinstance(intermediate, Repeated):
                # breakpoint()
                top_left = self.do_repeated(intermediate, img, composition, top_left)
                # breakpoint()
                continue
            elif isinstance(intermediate, Composition):
                # Recurse if you have an existing composition TODO
                intermediate_image = self.create_composition(intermediate.image)
            # elif isinstance(intermediate, IntermediateImage):
            #     offset = intermediate.offset
            #     piped = intermediate.piped
            #     if isinstance(intermediate.image, Repeated):
            #         intermediate_image = self.create_repeated(intermediate.image)
            #         breakpoint()
            #     else:
            else:
                intermediate_image = self.create_image(intermediate.image)
            # else:
            # raise ValueError("Invalid intermediate image")
            piped = DeferredOperation.Eval(intermediate.piped, self)
            offset = DeferredOperation.Eval(intermediate.offset, self)
            # Position
            if piped:
                print("(comp) piped")
                # NOTE: YOU DO NEED THIS AND IT IS DIFFERENT THAN THE REPEATED VERSION!
                paste_x = 0 + offset.x
                paste_y = 0 + offset.y
                # breakpoint()
            else:
                paste_x = top_left.x + offset.x
                paste_y = top_left.y + offset.y
            print(f"(comp) write to {paste_x}, {paste_y}")

            img.paste(
                intermediate_image,
                (
                    paste_x,
                    paste_y,
                    paste_x + intermediate.image.size.x,
                    paste_y + intermediate.image.size.y,
                ),
            )
            top_left.x = paste_x + intermediate.image.size.x
            if top_left.x >= size.x:
                top_left.x = 0
                top_left.y += intermediate.image.size.y
                if top_left.y >= size.y:
                    print("Composition size exceeded... doing nothing though")
        return img

    def run(self):
        # TODO: donot regenerate images already made, need to
        # explore the composition AST and substitute already compiled images
        # in there.
        for node in self.tree:
            # Will this subclass isinstance to IMImage? Either way do first
            if isinstance(node, Local):
                # Image is already generated and stored
                continue
            if isinstance(node, Composition):
                img = self.create_composition(node)
                img.show()
                self.generated_images[node.name] = img
            elif isinstance(node, IMImage):
                img = self.create_image(node)
                img.show()
                self.generated_images[node.name] = img
