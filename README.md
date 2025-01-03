# Imogen
A DSL for generating and composing images, with Pillow providing the rendering backend.

```
$ poetry install .
$ imogen examples/flag_se.img -p
```

![examples/random_colors.png]
```lua
local square_size = (512, 512)
local tile_size = (64, 64)

random_colors square_size #ffffff "Colored Square" {
    (0, 0) repeat tile_size.x // 8 {
        (0, 0) repeat tile_size.x // 8 {
            (0, 0) repeat tile_size.x // 8 {
                local r = ~random() * 256
                local g = ~random() * 256
                local b = ~random() * 256
                (0, 0) [ (32, 32) #(~int(r), ~int(g), ~int(b)) "" ]
            }
       }
    }
}
```

![examples/flag_se.png](flag_se.png)
```lua
-- Swedish Flag
local se_blue = #005293
local se_yell = #FFCD00

-- aspect ratios, horizontal and vertical
local imgh = 8
local imgv = 5

local h1 = 5
local h2 = 2
local h3 = 9

local v1 = 4
local v2 = 2
local v3 = 4

local scalef = 64

-- Define the properties of the base image: `name (width, height) background_color background_text { <composition> }`
flag_se (imgh * scalef, imgv * scalef) se_blue "" {

    -- Prepare dimension values
    -- The width-offset-aspect is 5:2:9, so we
    -- define an offset of 5 * scalef, and round to integer
    local aspect_ratio_w_px = (imgh*scalef//(h1+h2+h3))
    local flag_offset_x = int(aspect_ratio_w_px * h1)
    local cross_width = int(aspect_ratio_w_px * h2)

    local aspect_ratio_h_px = (imgv*scalef//(v1+v2+v3))
    local flag_offset_y = aspect_ratio_h_px * v1
    local cross_thick = aspect_ratio_h_px * v2

    -- Draw the vertical bar;
    -- Specify the actual composition by giving the (x, y) offset from (0, 0) (top left)
    -- and defining an anonymous (unnamed) image `[(width, height) color text]` to paste
    -- at the offset.
    (flag_offset_x, 0) [(cross_width, imgv * scalef) se_yell ""]

    -- Pipe operator restores the pointer to the top-left corner of the image,
    -- instead of writing the next image at the end of the current one.
    |>
    -- Draw the horizontal bar
    (0, flag_offset_y) [(imgh * scalef , cross_thick) se_yell ""]
}
```
# Why?

My original motivation was to easily generate distinct template/placeholder assets
for game development (give me 5 64x64 squares for different mob types) without having to learn / open a GUI photo/image editing program.

The composition paradigm Imogen uses has turned out to be pleasant to work with, but the main aspect that seems promising is allowing images to be compositional elements in other images, and establishing dependency graphs between images, so that changing an upstream image will also re-render the downstream image. So, for example, if you have a background image `image1.img` with color `purple`, and you use this image in the composition of another image `image2.img`, if the color of image1 is changed, we can rerender all of its downstream dependencies, including `image2.img1`. This has not been implemented yet, but is planned.

# Features

* Render images as PNGs to the filesystem
* Variables
* Syntactic sugar for colors: #(r,g,b) `#(100, 250, 134)`; HTML name `#red`; Hex `#ffeeaa`
* `local` and non-local image declarations, with `local` not being saved to the filesystem during rendering
* `repeat` for looping
* Loop variables for counting iteration
* stdlib hooks like `int` and `random`


# How?

Imogen works with a simple principle of "images" and "compositions", where an image is a named object with a size, background color, background text, and an optional composition; and a composition is a series of images to be *pasted* onto their parent image, starting from its top-left corner. Each time an image is pasted, the "top left corner" pointer moves to the bottom-right of the pasted image, wrapping according to the width of the parent image.

## Images

`my_image (128, 128) #f0ead6 "My Image"` will generate a 64-by-32 image with an "eggshell" background color and the text "My Image", and save it to the filesystem as `my_image.png`

If an image is prefixed with `local` e.g. `local my_image`, the image will render, but not be saved to the filesystem. This is useful when defining intermediate images to be used in compositions.

## Compositions

A composition is specified as a series of pairs of "offsets" and "images".
An offset is a value specifying the number of pixels to move down and right from (0,0),
the top-left corner of the base image the composition is working from.

This code

```lua
local my_image_tmp (64, 32) #red ""

my_image2 (128, 128) #f0ead6 "My Image" {
    (32, 0) my_image_tmp
}
```

Will produce a 32x32 image, with a red background, starting 32 pixels right and 0 pixels down from the top-left of its parent:

![examples/my_image2.png]

What is happening is that we've defined a `local` image, `my_image_tmp`, which is 64x32 with a red background and no text, and then specified in the composition section of `my_image2` (delimited by `{}`) that we should *paste* onto the parent image, starting from (0,0), but moving by an offset of (32, 0), before pasting.


# Known bugs
* `green` as a color will parse and be black, i.e we're parsing colors without a #
* some loop variables won't compute within expressions
* Pipe operator resets local var scope

# Upcoming Feature

* @param to export local vars to be provided with CLI invocation
* dependency graph between assets with caching and re-rendering only as needed
* GUI for tweaking @param exports and displaying render
* dynamic image sizes, where the final size of the asset is computed from the best fit of all its constituents
* right-hand-side offsets
* sugar where composition elements without prefixed tuple are (0,0) offset

