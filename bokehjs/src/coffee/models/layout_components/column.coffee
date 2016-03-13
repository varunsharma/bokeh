GridLayout = require "./grid_layout"

class ColumnView extends GridLayout.View
  className: "bk-grid-column"

class Column extends GridLayout.Model
  type: 'Column'
  default_view: ColumnView

  constructor: (attrs, options) ->
    super(attrs, options)
    @_horizontal = false

module.exports =
  View: ColumnView
  Model: Column
