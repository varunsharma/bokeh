kiwi = require "kiwi"
{Variable, Expression, Constraint, Operator } = kiwi
BokehView = require "../core/bokeh_view"
Model = require "../model"
{mixin_layoutable, GE, EQ, LE, WEAK_GE, WEAK_EQ, WEAK_LE} = require "./layoutable"
$ = require "jquery"
_ = require "underscore"
p = require "../core/properties"

class DemoWidgetView extends BokehView
  className: 'bk-demo-widget'

  initialize: (options) ->
    super(options)
    @listenTo(@model, 'change', @render)

    @_plot_element = $("<div class=\"bk-plot\" style=\"border: 1px solid black;\"></div>")
    @_title_element = $("<h4 style=\"margin: 0px; text-align: center;\"></h4>")
    @_left_axis_element = $("<div class=\"bk-left-axis\" style=\"border: 1px solid black;\"></div>")
    @_right_axis_element = $("<div class=\"bk-right-axis\" style=\"border: 1px solid black;\"></div>")
    @_bottom_axis_element = $("<div class=\"bk-bottom-axis\" style=\"border: 1px solid black;\"></div>")
    @$el.append(@_plot_element, @_title_element, @_left_axis_element, @_right_axis_element, @_bottom_axis_element)

    # handy for debugging
    @$el.prop('title', @model.id)

  render: () ->

    # The "-2" on widths and heights in here are for the 1px
    # borders. The CSS border is OUTSIDE the width/height, but
    # INSIDE the top/left position. So the position doesn't adjust
    # for border but the width/height does.

    @$el.css({
      position: 'absolute',
      background: @mget('background'),
      left: @mget('dom_left'),
      top: @mget('dom_top'),
      width: @model._width._value,
      height: @model._height._value
    });

    $(@_plot_element).css({
      position: 'absolute',
      left: @model._plot_left._value,
      top: @model._plot_top._value,
      # -2 is for the 1px css border
      width: @model._plot_right._value - @model._plot_left._value - 2,
      height: @model._plot_bottom._value - @model._plot_top._value - 2
    });

    $(@_title_element).text(@mget('title'))
    $(@_title_element).css({
      position: 'absolute',
      display: if @mget('title') != '' then 'block' else 'none'
      left: @model._plot_left._value,
      top: @model._plot_top._value - @model._title_height._value,
      width: @model._plot_right._value - @model._plot_left._value,
      height: @model._title_height._value
    })

    $(@_left_axis_element).css({
      position: 'absolute',
      display: if @mget('left_axis') then 'block' else 'none'
      left: @model._plot_left._value - @model._left_axis_width._value
      top: @model._plot_top._value
      # -2 is for the 1px css border
      width: @model._left_axis_width._value - 2 - 3 # 3 is so we aren't touching the plot
      height: @model._plot_bottom._value - @model._plot_top._value - 2
    })

    $(@_right_axis_element).css({
      position: 'absolute',
      display: if @mget('right_axis') then 'block' else 'none'
      left: @model._plot_right._value + 3 # 3 is so we aren't touching the plot
      top: @model._plot_top._value
      # -2 is for the 1px css border
      width: @model._right_axis_width._value - 2 - 3
      height: @model._plot_bottom._value - @model._plot_top._value - 2
    })

    $(@_bottom_axis_element).css({
      position: 'absolute',
      display: if @mget('bottom_axis') then 'block' else 'none'
      left: @model._plot_left._value
      top: @model._plot_bottom._value + 3 # 3 so we aren't touching the plot
      # -2 is for the 1px css border
      width: @model._plot_right._value - @model._plot_left._value - 2
      height: @model._bottom_axis_height._value - 2 - 3
    })


class DemoWidget extends Model

  default_view: DemoWidgetView

  constructor: (attrs, options) ->
    super(attrs, options)
    @set('dom_left', 0)
    @set('dom_top', 0)
    @_width = new Variable()
    @_height = new Variable()
    # these are the COORDINATES of the four plot sides
    @_plot_left = new Variable()
    @_plot_right = new Variable()
    @_plot_top = new Variable()
    @_plot_bottom = new Variable()
    # this is the DISTANCE FROM THE SIDE of the right and bottom,
    # since that isn't the same as the coordinate
    @_width_minus_plot_right = new Variable()
    @_height_minus_plot_bottom = new Variable()
    # these are the plot width and height, but written
    # as a function of the coordinates because we compute
    # them that way
    @_plot_right_minus_plot_left = new Variable()
    @_plot_bottom_minus_plot_top = new Variable()
    @_whitespace_left = new Variable()
    @_whitespace_right = new Variable()
    @_whitespace_top = new Variable()
    @_whitespace_bottom = new Variable()

    @_left_axis_width = new Variable()
    @_right_axis_width = new Variable()
    @_bottom_axis_height = new Variable()
    @_title_height = new Variable()

  props: ->
    return _.extend {}, super(), {
      background: [ p.String, 'white' ]
      title: [p.String, '']
      left_axis: [p.Bool, true]
      right_axis: [p.Bool, false]
      bottom_axis: [p.Bool, true]
      min_plot_width: [p.Number, 40]
      min_plot_height: [p.Number, 40]
    }

  get_constraints: () ->
    result = []

    # plot width and height are a function of plot sides...
    result.push(EQ([-1, @_plot_right], @_plot_left, @_plot_right_minus_plot_left))
    result.push(EQ([-1, @_plot_bottom], @_plot_top, @_plot_bottom_minus_plot_top))

    # min size, weak in case it doesn't fit
    result.push(WEAK_GE(@_plot_right_minus_plot_left, - @get('min_plot_width')))
    result.push(WEAK_GE(@_plot_bottom_minus_plot_top, - @get('min_plot_height')))

    # whitespace is weakly zero because we prefer to expand the
    # plot not the whitespace. Possible problem: if we discard
    # these constraints, would we then arbitrarily expand either
    # the plot or the whitespace?  Not sure how to say "expand
    # whitespace the minimum to meet constraints, prefer to expand
    # plot area"
    result.push(WEAK_EQ(@_whitespace_left))
    result.push(WEAK_EQ(@_whitespace_right))
    result.push(WEAK_EQ(@_whitespace_top))
    result.push(WEAK_EQ(@_whitespace_bottom))

    # whitespace has to be positive
    result.push(GE(@_whitespace_left))
    result.push(GE(@_whitespace_right))
    result.push(GE(@_whitespace_top))
    result.push(GE(@_whitespace_bottom))

    # Axes and title are hardcoded size if we are going to draw them at all
    if @get('left_axis')
      result.push(EQ(@_left_axis_width, -20))
    else
      result.push(EQ(@_left_axis_width))

    if @get('right_axis')
      result.push(EQ(@_right_axis_width, -20))
    else
      result.push(EQ(@_right_axis_width))

    if @get('bottom_axis')
      result.push(EQ(@_bottom_axis_height, -20))
    else
      result.push(EQ(@_bottom_axis_height))

    if @get('title') != ''
      result.push(EQ(@_title_height, -25))
    else
      result.push(EQ(@_title_height))

    # plot has to be inside the width/height
    result.push(GE(@_plot_left))
    result.push(GE(@_width, [-1, @_plot_right]))
    result.push(GE(@_plot_top))
    result.push(GE(@_height, [-1, @_plot_bottom]))

    # plot sides align with the sum of the stuff outside the plot
    result.push(EQ(@_whitespace_left, @_left_axis_width, [-1, @_plot_left]))
    result.push(EQ(@_plot_right, @_right_axis_width, @_whitespace_right, [-1, @_width]))
    result.push(EQ(@_whitespace_top, @_title_height, [-1, @_plot_top]))
    result.push(EQ(@_plot_bottom, @_bottom_axis_height, @_whitespace_bottom, [-1, @_height]))

    # compute plot bottom/right indent
    result.push(EQ(@_height_minus_plot_bottom, [-1, @_height], @_plot_bottom))
    result.push(EQ(@_width_minus_plot_right, [-1, @_width], @_plot_right))

    return result

  get_constrained_variables: () ->
    {
      'width' : @_width,
      'height' : @_height
      # when this widget is on the edge of a box visually,
      # align these variables down that edge
      'on-top-edge-align' : @_plot_top
      'on-bottom-edge-align' : @_height_minus_plot_bottom
      'on-left-edge-align' : @_plot_left
      'on-right-edge-align' : @_width_minus_plot_right
      # when this widget is in a box cell with the same "arity
      # path" as a widget in another cell, align these variables
      # between the two box cells
      'on-top-cell-align' : @_plot_top
      'on-bottom-cell-align' : @_height_minus_plot_bottom
      'on-left-cell-align' : @_plot_left
      'on-right-cell-align' : @_width_minus_plot_right
      # when this widget is in a box, make these variables
      # the same size as these variables in the rest of the box
      'box-equal-size-horizontal' : @_plot_right_minus_plot_left
      'box-equal-size-vertical' : @_plot_bottom_minus_plot_top
    }

  get_layoutable_children: () ->
    []

  set_dom_origin: (left, top) ->
    @set({ dom_left: left, dom_top: top })

  variables_updated: () ->
    # hack to force re-render
    @trigger('change')

mixin_layoutable(DemoWidget)

module.exports =
  Model: DemoWidget
