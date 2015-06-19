_ = require "underscore"
$ = require "jquery"

ContinuumView = require "../common/continuum_view"
HasProperties = require "../common/has_properties"

class ErrorPanelView extends ContinuumView
  initialize: (options) ->
    super(options)
    @$el.addClass("bk-error-panel")
    @$el.empty()
    @render()

  render: () ->
    if @mget("visible")
       @$el.show() # TODO animate this
    else
       @$el.hide()
    @$el.html("<h2>Error in application</h2><pre></pre>")
    @$el.children("pre").text(@mget("error"))
    return @

class ErrorPanel extends HasProperties
  type: "ErrorPanel"
  default_view: ErrorPanelView

  defaults: () ->
    return _.extend {}, super(), {
      visible: false,
      error: ""
    }

module.exports =
  Model: ErrorPanel
  View: ErrorPanelView
