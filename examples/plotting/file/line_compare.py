""" Compare WebGL with canvas line.

"""

import numpy as np

from bokeh.models import Slider, Dropdown, HBox, VBox, CustomJS
from bokeh.plotting import Figure, show, output_file

p1 = Figure(title="Canvas", webgl=False)

p2 = Figure(title="WebGL", webgl=True)

ys = 10  # yscale, to increase anisotropy

lines = []
for p in (p1, p2):

    t = np.linspace(0, 2 * np.pi, 50)
    x = np.sin(t) * 10
    y = np.cos(t) * 10
    l1 = p.line(x, y * ys, color="#2222aa",
                line_width=6, line_cap='butt',
                line_join='round', line_dash=(10, 6, 3, 6, 3, 6))

    t = np.arange(10)
    t = np.linspace(0, 4 * np.pi, 150)
    x = t - 5
    y = (t + 1) * ((t % 2) * 2 - 1)
    y = np.sin(t) + 5
    l2 = p.line(x, y * ys, color="#22aa22",
                line_width=6, line_cap='butt', line_join='round')

    t = np.arange(10)
    x = t - 5
    y = 0.3 * (t + 1) * ((t % 2) * 2 - 1) - 6
    l3 = p.line(x, y * ys, color="#aa2222",
                line_width=6, line_cap='butt',
                line_join='round', line_dash=(10, 10))
    l4 = p.line(y, x * ys, color="#aa2222",
                line_width=6, line_cap='butt',
                line_join='round', line_dash=(10, 10))
    
    lines.extend([l1, l2, l3, l4])

def add_callback(widget, prop):
    widget.callback = CustomJS(args=dict(widget=widget), code="""
        for ( var i = 0; i < %s; i++ ) {
            var g = eval( 'line' + i ).get( 'glyph' );
            g.set( '%s', widget.get( 'value' ) );
            window.g = g;
        }
        """ % (len(lines), prop))
    for i, line in enumerate(lines):
        widget.callback.args['line%i' % i] = line

def make_slider(prop, start, end, value):
    slider = Slider(title=prop, start=start, end=end, value=value)
    add_callback(slider, prop)
    return slider

def make_dropdown(prop, menu):
    dropdown = Dropdown(label=prop, menu=menu)
    add_callback(dropdown, prop)
    return dropdown

sliders = [
    make_slider('line_width', start=0.2, end=16, value=5),
    make_slider('line_dash_offset', start=0, end=100, value=1),
    make_dropdown('line_cap', [("butt", "butt"), ("round", "round"), ("square", "square")]),
    make_dropdown('line_join', [("miter", "miter"), ("round", "round"), ("bevel", "bevel")]),
]

sliders = VBox(*sliders)

output_file("line_compare.html", title="line_compare.py example")

show(HBox(sliders, p1, p2))
