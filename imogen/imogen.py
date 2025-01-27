from pathlib import Path

from imogen.parser import parser, ImageTransformer

from imogen.render import Render
from pprint import pprint


# TODO:
# absolute offset: !() is offest from top left
# extern: comes in from CLI instead of local
import logging

logger = logging.getLogger(__name__)


def run(file, **kwargs):
    with open(file) as f:
        code = f.read()
    parse = parser.parse(code)
    transformed = ImageTransformer()
    tree = transformed.transform(parse)
    logger.debug(tree)

    r = Render(tree, {"vars": transformed.vars}, **kwargs)
    r.run()


# parsed = parser.parse(gamedev)
# # print(parsed)
# transformed = ImageTransformer()
# tree = transformed.transform(parsed)
# from pprint import pprint

# pprint(tree)

# r = Runner(tree, {"vars": transformed.vars})

# r.run()
# pprint(r.metadata)
# for node in transformed:
#     if isinstance(node, Composition):
#         create_composition(node).show()
#     else:
#         pass
#         # create_image(node).show()
#     # print(node)
# if isinstance(node, IMImage):
#     print(node)
# else:
#     print(node.name)
#     for img in node.composition:
#         print(img.image)
#         print(img.offset)
#         print()
# print()
# for name, img in transformed.items():
# Create IMImage objects and Composition objects and save them
# _image = create_image(img)

# parser = ImageTransformer()
# parser.transform(parsed)
# Create and display the composition image
# composition = parser.transformer.compositions['composition']
# res = create_composition(composition)
# res.show()
