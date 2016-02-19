Box = require "./box"

class Column extends Box.Model
  type: 'Column'

  constructor: (attrs, options) ->
    super(attrs, options)
    @_horizontal = false

module.exports =
  Model: Column

