Box = require "./box"

class Row extends Box.Model
  type: 'Row'

  constructor: (attrs, options) ->
    super(attrs, options)
    @_horizontal = true

module.exports =
  Model: Row

