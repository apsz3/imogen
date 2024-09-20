from PIL import Image, ImageDraw
from imogen.objs import (
    Composition,
    DeferredOperation,
    IMImage,
    IntermediateImage,
    Local,
    Point,
    Repeated,
)


class Render:

    def evaluate(self, node):
        if isinstance(node, DeferredOperation):
            return node.evaluate(self)
        return node

    def __init__(self, tree, metadata):
        self.tree = tree
        self.metadata = metadata
        self.generated_images = {}

    def create_image(self, image: IMImage) -> Image:
        img = Image.new("RGB", (image.size.x, image.size.y), image.color)
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), image.text, fill=(0, 0, 0))
        return img

    def do_repeated(
        self, repeated: Repeated, img: Image, comp: Composition, top_left: Point
    ):
        # breakpoint()
        for i in range(repeated.count):
            # Generate all the images
            if repeated.loop_var:
                self.metadata[repeated.loop_var] = i
            _rimg: IntermediateImage
            for _rimg in repeated.body:
                # HANDLE NESTING HERE
                if isinstance(_rimg, Repeated):
                    top_left = self.do_repeated(_rimg, img, comp, top_left)
                    continue

                piped = _rimg.piped
                offset = _rimg.offset  # Already has the repeat global offset
                _rimg_img: IMImage = _rimg.image
                _real_img = self.create_image(_rimg_img)
                if piped:
                    paste_x = 0
                    paste_y = 0
                else:
                    paste_x = top_left.x + offset.x
                    paste_y = top_left.y + offset.y
                    print(f"write to {paste_x}, {paste_y}")
                img.paste(
                    _real_img,
                    (
                        paste_x,
                        paste_y,
                        paste_x + _rimg_img.size.x,
                        paste_y + _rimg_img.size.y,
                    ),
                )
                top_left.x = paste_x + _rimg_img.size.x
                if top_left.x >= comp.size.x:
                    top_left.x = 0
                    top_left.y += _rimg_img.size.y
                    if top_left.y >= comp.size.y:
                        print("Composition size exceeded... doing nothing though")
        return top_left

    # Write code that will take a Composition object and create a PIL image
    # REPEATED THINGS ARE NOT RELATIVE -- THEY ARE NOT SCOPED! THEY ARE SCOPED TO THE PARENT COMPOSITION!
    # FOR SCOPING, USE COMPOSITIONS!
    def create_composition(self, composition: Composition) -> Image:
        img = Image.new(
            "RGB", (composition.size.x, composition.size.y), composition.color
        )
        top_left = Point(0, 0)

        # Insert repeated image code into the middle of the composition list where it appears

        # TODO: Extend the composition images with the body of the repeater,
        # but also track which instruction is a repeat; keep a stack of repeats,
        # and increment loop variables awccordingly. Need to flatten this
        # so that pipes work?

        for intermediate in composition.composition:
            intermediate_image = None
            if isinstance(intermediate, Repeated):
                top_left = self.do_repeated(intermediate, img, composition, top_left)
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
            piped = intermediate.piped
            offset = intermediate.offset
            # Position
            if piped:
                paste_x = 0 + offset.x
                paste_y = 0 + offset.y
                # breakpoint()
            else:
                paste_x = top_left.x + offset.x
                paste_y = top_left.y + offset.y
                print(f"write to {paste_x}, {paste_y}")

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
            if top_left.x >= composition.size.x:
                top_left.x = 0
                top_left.y += intermediate.image.size.y
                if top_left.y >= composition.size.y:
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
