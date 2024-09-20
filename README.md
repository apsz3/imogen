# Known bugs
* `green` as a color will parse and be black, i.e we're parsing colors without a #

# Features TODO

* `<name> ? ...` which will fit-to-size the image to its constituents
* binding loop variables
* right-hand-side offsets
* sugar where composition elements without prefixed tuple are (0,0) offset


Introduce different annotations for parameters.
Tweak = it goes into the UI. For example, if we have a fractional offset of where we place something, you want to make that tweakable. Same for colors.
export text = "Default text"
Type check on the default, tells you what to have in the GUI, e.g. text input, slider, knob, bool, etc.
knob / switch etc compile to the gui you get.
switch is bool knob is range, textinput , etc.
Export = modifiable in gui
Extern = inputted with CLI... can also be modified in gui?
Maybe just extend for extension
ext text = "yeet"
ext size = (512, 512)
