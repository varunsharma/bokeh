GridLayout = require "./grid_layout"

class RowView extends GridLayout.View
  className: "bk-grid-row"

class Row extends GridLayout.Model
  type: 'Row'
  default_view: RowView

  constructor: (attrs, options) ->
    super(attrs, options)
    @_horizontal = true

module.exports =
  View: RowView
  Model: Row
