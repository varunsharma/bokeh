_ = require "underscore"
HasParent = require "../../common/has_parent"
PlotWidget = require "../../common/plot_widget"
{fixup_context} = require "../../common/canvas"
{logger} = require "../../common/logging"
properties = require "../../common/properties"

class SpanView extends PlotWidget

  tagName: 'canvas'

  initialize: (options) ->
    super(options)
    @line_props = new properties.Line({obj: @model, prefix: ''})
    @ctx = fixup_context(@$el[0].getContext('2d'))
    @$el.appendTo(@plot_view.$el.find('div.bk-canvas-overlays'))
    @$el.css({position: 'absolute'})
    @$el.hide()

  bind_bokeh_events: () ->
    @listenTo(@model, 'change:location', () => @render())

  render: () ->
    if not @mget('location')?
      @$el.hide()
      return

    dim = @mget('dimension')
    frame = @plot_model.get('frame')
    canvas = @plot_model.get('canvas')
    xmapper = @plot_view.frame.get('x_mappers')[@mget("x_range_name")]
    ymapper = @plot_view.frame.get('y_mappers')[@mget("y_range_name")]

    if dim == 'width'
      stop = canvas.vy_to_sy(@_calc_dim(@mget('location'), ymapper))
      sleft = canvas.vx_to_sx(frame.get('left'))
      width = frame.get('width')
      height = @mget('line_width')
    else
      stop = canvas.vy_to_sy(frame.get('top'))
      sleft = canvas.vx_to_sx(@_calc_dim(@mget('location'), xmapper))
      width = @mget('line_width')
      height = frame.get('height')

    @$el.attr({
      width: width
      height: height
    })
    @$el.css({
      top: stop
      left: sleft
      width: "#{width}px"
      height: "#{height}px"
      zIndex: 1000
    })

    @ctx.save()
    @ctx.clearRect(0, 0, width, height)
    @ctx.beginPath()
    @line_props.set_value(@ctx)
    @ctx.moveTo(0, 0)
    if dim == "width"
      @ctx.lineTo(width, 0)
    else
      @ctx.lineTo(0, height)
    @ctx.stroke()
    @ctx.restore()

    @$el.show()

  _calc_dim: (location, mapper) ->
      if @mget('location_units') == 'data'
        vdim = mapper.map_to_target(location)
      else
        vdim = location
      return vdim

class Span extends HasParent
  default_view: SpanView
  type: 'Span'

  defaults: ->
    return _.extend {}, super(), {
      x_range_name: "default"
      y_range_name: "default"
      location_units: "data"
    }

  display_defaults: ->
    return _.extend {}, super(), {
      level: 'annotation'
      dimension: "width"
      location: null
      line_color: 'black'
      line_width: 1
      line_alpha: 1.0
      line_dash: []
      line_dash_offset: 0
      line_cap: "butt"
      line_join: "miter"
    }

module.exports =
  Model: Span
  View: SpanView
