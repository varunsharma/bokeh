"""This is the Bokeh charts interface. It gives you a high level API to build
complex plot is a simple way.

This is the main Chart class which is able to build several plots using the low
level Bokeh API. It setups all the plot characteristics and lets you plot
different chart types, taking OrderedDict as the main input. It also supports
the generation of several outputs (file, server, notebook).
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2012 - 2014, Continuum Analytics, Inc. All rights reserved.
#
# Powered by the Bokeh Development Team.
#
# The full license is in the file LICENSE.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import absolute_import

import warnings
from collections import defaultdict
import numpy as np

from ..core.enums import enumeration, LegendLocation

from ..models import (
    CategoricalAxis, DatetimeAxis, Grid, Legend, LinearAxis, Plot,
    HoverTool, FactorRange, Axis, Range1d
)
from ..plotting import DEFAULT_TOOLS
from ..plotting.helpers import _process_tools_arg
from ..core.properties import (Auto, Bool, Either, Enum, Int, Float,
                               String, Tuple, Override, Instance, Dict)

from ..util.deprecate import deprecated

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

Scale = enumeration('linear', 'categorical', 'datetime')

def create_axes(plot, dim):

    lin_kwargs = {dim + '_range_name': dim + '_lin_range', 'plot': plot}
    cat_kwargs = {dim + '_range_name': dim + '_cat_range', 'plot': plot}

    return {'linear': LinearAxis(**lin_kwargs),
            'categorical': CategoricalAxis(**cat_kwargs),
            'datetime': DatetimeAxis(**lin_kwargs)}

def create_ranges(dim):
    return {'categorical': FactorRange(factors=['a', 'b']), 'linear': Range1d(start=0,
                                                                              end=1)}

class ChartDefaults(object):
    def apply(self, chart):
        """Apply this defaults to a chart."""

        if not isinstance(chart, Chart):
            raise ValueError("ChartsDefaults should be only used on Chart \
            objects but it's being used on %s instead." % chart)

        all_props = set(chart.properties_with_values(include_defaults=True))
        dirty_props = set(chart.properties_with_values(include_defaults=False))
        for k in list(all_props.difference(dirty_props)) + \
            list(chart.__deprecated_attributes__):
            if k == 'tools':
                value = getattr(self, k, True)
                if getattr(chart, '_tools', None) is None:
                    chart._tools = value
            else:
                if hasattr(self, k):
                    setattr(chart, k, getattr(self, k))

defaults = ChartDefaults()

class Chart(Plot):
    """ The main Chart class, the core of the ``Bokeh.charts`` interface.

    """

    __view_model__ = "Plot"
    __subtype__ = "Chart"

    legend = Either(Bool, Enum(LegendLocation), Tuple(Float, Float), help="""
    A location where the legend should draw itself.
    """)

    xgrid = Either(Bool, Instance(Grid), default=True, help="""
    Whether to draw an x-grid.
    """)

    ygrid = Either(Bool, Instance(Grid), default=True, help="""
    Whether to draw an y-grid.
    """)

    xlabel = String(None, help="""
    A label for the x-axis. (default: None)
    """)

    ylabel = String(None, help="""
    A label for the y-axis. (default: None)
    """)

    xscale = Either(Auto, Enum(Scale), help="""
    What kind of scale to use for the x-axis.
    """)

    yscale = Either(Auto, Enum(Scale), help="""
    What kind of scale to use for the y-axis.
    """)

    title_text_font_size = Override(default={ 'value' : '14pt' })

    responsive = Override(default=False)

    _defaults = defaults

    _xaxis = None
    _yaxis = None

    xaxes = Dict(String, Instance(Axis), default=None)
    yaxes = Dict(String, Instance(Axis), default=None)

    grids = Dict(String, Instance(Grid))
    x_cat_range = Instance(FactorRange, default=FactorRange())
    y_cat_range = Instance(FactorRange, default=FactorRange())

    x_lin_range = Instance(Range1d, default=Range1d())
    y_lin_range = Instance(Range1d, default=Range1d())

    __deprecated_attributes__ = ('filename', 'server', 'notebook', 'width', 'height')

    def __init__(self, *args, **kwargs):
        # pop tools as it is also a property that doesn't match the argument
        # supported types
        tools = kwargs.pop('tools', None)
        super(Chart, self).__init__(*args, **kwargs)

        defaults.apply(self)

        if tools is not None:
            self._tools = tools

        # TODO (fpliger): we do this to still support deprecated document but
        #                 should go away when __deprecated_attributes__ is empty
        for k in self.__deprecated_attributes__:
            if k in kwargs:
                setattr(self, k, kwargs[k])

        # TODO (bev) have to force serialization of overriden defaults on subtypes for now
        self.title_text_font_size = "10pt"
        self.title_text_font_size = "14pt"

        self._glyphs = []
        self._built = False

        self._builders = []
        self._renderer_map = []
        self._hover_tool = None
        self._ranges = defaultdict(list)
        self._labels = defaultdict(list)
        self._scales = defaultdict(list)
        self._tooltips = []

        self.create_tools(self._tools)

        if self.xaxes is None:
            self.xaxes = create_axes(self, 'x')
            self.renderers += list(self.xaxes.values())

        if self.yaxes is None:
            self.yaxes = create_axes(self, 'y')
            self.renderers += list(self.yaxes.values())

        if self.xgrid:
            self.grids['x'] = Grid(dimension=0)
            self.add_layout(self.grids['x'])

        if self.ygrid:
            self.grids['y'] = Grid(dimension=1)
            self.add_layout(self.grids['y'])

        self.extra_x_ranges = {'x_cat_range': self.x_cat_range,
                               'x_lin_range': self.x_lin_range}

        self.extra_y_ranges = {'y_cat_range': self.y_cat_range,
                               'y_lin_range': self.y_lin_range}

    def add_renderers(self, builder, renderers):
        self.renderers += renderers
        self._renderer_map.extend({ r._id : builder for r in renderers })

    def add_builder(self, builder):
        self._builders.append(builder)
        builder.create(self)

    def add_ranges(self, dim, range):
        self._ranges[dim].append(range)

    def add_labels(self, dim, label):
        self._labels[dim].append(label)

    def add_scales(self, dim, scale):
        self._scales[dim].append(scale)

    def add_tooltips(self, tooltips):
        self._tooltips += tooltips

    def _get_labels(self, dim):
        if not getattr(self, dim + 'label') and len(self._labels[dim]) > 0:
            return self._labels[dim][-1]
        else:
            return getattr(self, dim + 'label')

    def set_axes(self):
        """Set the axes based on the last scale type provided from builders."""
        for renderer in self.renderers:
            if isinstance(renderer, Axis):
                renderer.visible = False

        self._xaxis = self.get_axis('x', self._scales['x'][-1], self._get_labels('x'))
        self._xaxis.visible = True
        self.below = [self._xaxis]

        self._yaxis = self.get_axis('y', self._scales['y'][-1], self._get_labels('y'))
        self._yaxis.visible = True
        self.left = [self._yaxis]

    def create_grids(self):
        self.make_grid(0, self._xaxis.ticker)
        self.make_grid(1, self._yaxis.ticker)

    def create_tools(self, tools):
        """Create tools if given tools=True input.

        Only adds tools if given boolean and does not already have
        tools added to self.
        """

        if isinstance(tools, bool) and tools:
            tools = DEFAULT_TOOLS
        elif isinstance(tools, bool):
            # in case tools == False just exit
            return

        if len(self.tools) == 0:
            # if no tools customization let's create the default tools
            tool_objs = _process_tools_arg(self, tools)
            self.add_tools(*tool_objs)

    def start_plot(self):
        """Add the axis, grids and tools
        """

        self.set_axes()
        self.create_grids()

        # Add tools if supposed to
        if self.tools:
            self.create_tools(self.tools)

        if len(self._tooltips) > 0:
            if self._hover_tool is None:
                self._hover_tool = HoverTool(tooltips=self._tooltips)
                self.add_tools(self._hover_tool)
            else:
                # ToDo: this is not being sent by server because it is "client-only"
                self._hover_tool.tooltips = self._tooltips

    def update(self, **kwargs):
        self._tooltips = []
        self._ranges.clear()
        self._scales.clear()
        self._labels.clear()
        super(Chart, self).update(**kwargs)

    def add_legend(self, legends):
        """Add the legend to your plot, and the plot to a new Document.

        It also add the Document to a new Session in the case of server output.

        Args:
            legends(List(Tuple(String, List(GlyphRenderer)): A list of
                tuples that maps text labels to the legend to corresponding
                renderers that should draw sample representations for those
                labels.
        """
        location = None
        if self.legend is True:
            location = "top_left"
        else:
            location = self.legend

        if location:
            legend = Legend(location=location, legends=legends)
            self.add_layout(legend)

    def get_axis(self, dim, scale, label):
        """Create linear, date or categorical axis depending on the location,
        scale and with the proper labels.

        Args:
            location(str): the space localization of the axis. It can be
                ``left``, ``right``, ``above`` or ``below``.
            scale (str): the scale on the axis. It can be ``linear``, ``datetime``
                or ``categorical``.
            label (str): the label on the axis.

        Return:
            axis: Axis instance
        """

        data_range = self._ranges[dim][-1]

        if scale == "auto":
            if isinstance(data_range, FactorRange):
                scale = 'categorical'
            else:
                scale = 'linear'

        axes = getattr(self, dim + 'axes')

        if scale == "linear":
            range_name = dim + '_lin_range'
            axis = axes['linear']
            range = getattr(self, range_name)
            range.start = data_range[0]
            range.end = data_range[1]
        elif scale == "datetime":
            range_name = dim + '_lin_range'
            axis = axes['datetime']
            range = getattr(self, range_name)
            range.start = data_range[0]
            range.end = data_range[1]
        elif scale == "categorical":
            range_name = dim + '_cat_range'
            axis = axes['categorical']
            axis.major_label_orientation = np.pi / 4
            range = getattr(self, range_name)
            range.update(factors=data_range)
        else:
            range_name = dim + '_lin_range'
            axis = axes['linear']
            range = getattr(self, range_name)
            range.start = data_range[0]
            range.end = data_range[1]

        axis.axis_label = label

        setattr(self, dim + '_range', range)

        return axis

    def set_ranges(self):
        for dim in list(self._ranges.keys()):
            data_range = self._ranges[dim][-1]
            setattr(self, dim + '_range', data_range)

    def make_grid(self, dimension, ticker):
        """Create the grid just passing the axis and dimension.

        Args:
            dimension(int): the dimension of the axis, ie. xaxis=0, yaxis=1.
            ticker (obj): the axis.ticker object

        Return:
            grid: Grid instance
        """
        if dimension == 0:
            dim = 'x'
        else:
            dim = 'y'

        grid = getattr(self, dim + 'grid')
        if grid:
            pass
            self.grids[dim].ticker = ticker

    @property
    def filename(self):
        warnings.warn("Chart property 'filename' was deprecated in 0.11 \
            and will be removed in the future.")
        from bokeh.io import output_file
        output_file("default.html")

    @filename.setter
    def filename(self, filename):
        warnings.warn("Chart property 'filename' was deprecated in 0.11 \
            and will be removed in the future.")
        from bokeh.io import output_file
        output_file(filename)

    @property
    def server(self):
        warnings.warn("Chart property 'server' was deprecated in 0.11 \
            and will be removed in the future.")
        from bokeh.io import output_server
        output_server("default")

    @server.setter
    def server(self, session_id):
        warnings.warn("Chart property 'server' was deprecated in 0.11 \
            and will be removed in the future.")
        from bokeh.io import output_server
        if session_id:
            if isinstance(session_id, bool):
                session_id='default'
            output_server(session_id)

    @property
    def notebook(self):
        warnings.warn("Chart property 'notebook' was deprecated in 0.11 \
            and will be removed in the future.")
        from bokeh.io import output_notebook
        output_notebook()

    @notebook.setter
    def notebook(self, flag):
        warnings.warn("Chart property 'notebook' was deprecated in 0.11 \
            and will be removed in the future.")
        from bokeh.io import output_notebook
        output_notebook()

    @deprecated("Bokeh 0.11", "bokeh.io.show")
    def show(self):
        import bokeh.io
        bokeh.io.show(self)

    @property
    def width(self):
        warnings.warn("Chart property 'width' was deprecated in 0.11 \
            and will be removed in the future.")
        return self.plot_width

    @width.setter
    def width(self, width):
        self.plot_width = width

    @property
    def height(self):
        warnings.warn("Chart property 'height' was deprecated in 0.11 \
            and will be removed in the future.")
        return self.plot_height

    @height.setter
    def height(self, height):
        self.plot_height = height
