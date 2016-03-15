from __future__ import print_function

from numpy import pi, sin, cos, linspace, tan  # noqa

from bokeh.util.browser import view
from bokeh.document import Document
from bokeh.embed import file_html
from bokeh.models.glyphs import Line
from bokeh.models import (
    Plot, DataRange1d, LinearAxis, ColumnDataSource,
    PanTool, WheelZoomTool, ResizeTool, Row, Column
)

from bokeh.resources import INLINE

x = linspace(-2 * pi, 2 * pi, 10)

source = ColumnDataSource(
    data=dict(
        x=x,
        y1=sin(x),
        y2=cos(x),
        y3=tan(x),
        y4=sin(x) * cos(x),
    )
)


def make_plot(
    source,
    xname, yname,
    line_color,
    plot_width=200, plot_height=300,
    left_axis=True, right_axis=False,
    title=None
):
    xdr = DataRange1d()
    ydr = DataRange1d()
    plot = Plot(
        x_range=xdr, y_range=ydr, plot_width=plot_width, plot_height=plot_height,
        title=title, responsive=True,
        min_border_top=5, min_border_left=5, min_border_right=5, min_border_bottom=5,
    )
    plot.add_layout(LinearAxis(), 'below')
    if left_axis:
        plot.add_layout(LinearAxis(), 'left')
    if right_axis:
        plot.add_layout(LinearAxis(), 'right')
    plot.add_glyph(source, Line(x=xname, y=yname, line_color=line_color))
    plot.add_tools(PanTool(), WheelZoomTool(), ResizeTool())
    return plot

plot1 = make_plot(source, "x", "y1", "blue", plot_width=400, plot_height=300, title="Plot1")
plot2 = make_plot(source, "x", "y2", "red", plot_width=200, plot_height=150, title="Plot2")
plot3 = make_plot(source, "x", "y3", "green", left_axis=False, right_axis=True, plot_height=100)
plot4 = make_plot(source, "x", "y4", "pink", left_axis=False, title="Plot4")

row1 = Row(children=[plot1, plot2])
row2 = Row(children=[plot3, plot4])
column = Column(children=[row1, row2])

doc = Document()
doc.add_root(column)

if __name__ == "__main__":
    filename = "row.html"
    with open(filename, "w") as f:
        f.write(file_html(doc, INLINE, "New Grid Example"))
    print("Wrote %s" % filename)
    view(filename)
