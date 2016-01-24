from bokeh.models.widgets import HBox, VBoxForm, Select
from bokeh.io import curdoc, curstate

from six import iteritems


def kwargs_from_selectors(selectors):
    """ Produces kwargs from selectors for use in updating an interactive chart.

    Args:
        selectors (list(`~bokeh.models.widgets.Select`)): a list of selectors

    Returns:

    """
    return {name: selector.value for name, selector in iteritems(selectors)}


def generate_selectors(data, dims, attrs):
    """ Produce a list of selectors to be used for an interactive chart.

    Both dimensions and attribute specs are used to visually assign dimensions of data
    to components of a chart. Both are used to create selectors for the chart.

    Args:
        data (`~pandas.DataFrame`): the data used for the chart
        dims (list(`~bokeh.charts.properties.Dimension`)): list of dimensions
        attrs (list(`~bokeh.charts.attributes.AttrSpec`)): list of attribute specs

    Returns:

    """
    all_dims = {}
    all_dims.update(dims)
    all_dims.update(attrs)
    selectors = {}

    for dim_name, dim in iteritems(all_dims):
        selectors[dim_name] = generate_selector_from_dimension(dim, data,
                                                               columns=list(
                                                                       data.columns),
                                                               name=dim_name)

    return selectors


def generate_selector_from_dimension(dim, data, columns=None, default=None,
                                     default_type=None, name=None):
    """ Takes a dimension/attribute and data and produces a selector for it.

    ToDo: inspect the dimension for column types accepted and only add those columns to
        the options for the selector.

    Args:
        dim (`~bokeh.charts.properties.Dimension`): a dimension of a chart
        data (`~pandas.DataFrame`): the data associated with the chart
        columns (list(str), optional): list of columns, taken from data if not provided
        default (str, optional): the default column to use for the selector
        default_type (str, optional): can be used to select the first column that meets
            the type criteria, instead of specifying `default`
        name (str, optional): the name to provide the selector, taken from `dim.name`
            if not provided.

    Returns:
        `~bokeh.models.widgets.Select`

    """
    if columns is None and data is not None:
        if not hasattr(data, columns):
            raise ValueError('If passing data without columns, data must have columns.')
        columns = list(data.columns)

    if default is None:
        default = columns[0]

    if name is None:
        name = dim.name

    return Select(
            title=name,
            name=name + '_select',
            options=columns,
            value=default
    )


def interact(chart, data, selectors=None, **kwargs):
    """ Produces a quick interactive chart app.

    Because charts uses the column-oriented interface, most attributes and dimensions
    are consistent in the way that they accept inputs. This consistency can be utilized
    to encapsulate the generic functionality needed to produce an interactive chart.
    Any dimension or attribute that is defined as part of the chart is set to have its
    own selector to choose the column to assign to it.

    Args:
        chart (`~bokeh.charts.chart.Chart`): the chart class to interact with
        data (`~pandas.DataFrame`): the data to use for the chart
        selectors (list(str), optional): list of names of dimensions or attributes to use
            for the chart. This is optional because if not provided, all dimensions
            and attributes will receive a selector.
        **kwargs: any other kwargs to be passed to the chart

    Examples:
        from bokeh.charts import interact, Bar
        import pandas as pd

        data = {'a': [1, 2, 3, 4],
                'b': [3, 5, 4, 5],
                'c': ['foo', 'bar', 'foo', 'bar']}

        interact(Bar, pd.DataFrame(data), selectors=['values', 'label'],
                 tooltips=[('value', '@height')])

    """

    # don't want to autoadd the chart because we are provided our own layout
    # ToDo: shouldn't use the private attribute here, see issue #3638
    curstate()._autoadd = False

    dimensions = {}
    attributes = {}

    # collect dimensions and attributes to create selectors
    for builder in chart.builders:
        for dim_name in builder.dimensions:
            dimensions[dim_name] = getattr(builder, dim_name)

        attributes.update(builder.default_attributes)

    # filter down to provided selector names as requested
    if selectors is not None:
        dimensions = {dim_name: dim for dim_name, dim in iteritems(dimensions)
                      if dim_name in selectors}
        attributes = {dim_name: dim for dim_name, dim in iteritems(attributes)
                      if dim_name in selectors}

    # get selectors and add to the layout
    selectors = generate_selectors(data, dimensions, attributes)
    inputs = VBoxForm(children=list(selectors.values()))

    # kwargs are constant kwargs passed in plus the selector values
    chart_kwargs = kwargs
    chart_kwargs.update(kwargs_from_selectors(selectors))

    # create initial chart and add inputs and chart to layout
    plot = chart(data, **chart_kwargs)
    hbox = HBox(children=[inputs, plot])

    # collect the chart renderers for passing back into subsequent chart updates
    chart_renderers = [renderer for renderer in plot.renderers if
                       hasattr(renderer, 'glyph')]
    chart_renderers = {renderer.glyph.__class__.__name__.lower(): renderer for renderer in
                       chart_renderers}

    # add chart renderers and chart to kwargs so we don't recreate them each time
    chart_kwargs['renderers'] = chart_renderers
    chart_kwargs['chart'] = plot

    def update_chart():
        # get updated kwargs from selectors and update chart
        chart_kwargs.update(kwargs_from_selectors(selectors))
        chart(data, **chart_kwargs)

    def input_change(attrname, old, new):
        update_chart()

    # hook up callbacks for selectors
    for selector in list(selectors.values()):
        selector.on_change('value', input_change)

    # add the interactive chart with inputs and chart to root of document
    curdoc().add_root(hbox)
