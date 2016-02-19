_ = require "underscore"
kiwi = require "kiwi"
{Variable, Expression, Constraint, Operator } = kiwi
{Eq, Le, Ge} = Operator
p = require "../core/properties"

class Layoutable

  _constraints_invalid: true
  _paint_invalid: true

  constraints_invalid: () ->
    return @_constraints_invalid

  paint_invalid: () ->
    return @_paint_invalid

  invalidate_constraints: () ->
    @_constraints_invalid = true

  invalidate_paint: () ->
    @_paint_invalid = true

  validate_constraints: () ->
    @_constraints_invalid = true

  validate_paint: () ->
    @_paint_invalid = true

mixin_layoutable = (klass) ->
  proto = klass.prototype

  for method in ['get_constraints', 'get_constrained_variables', 'get_layoutable_children',
                 'set_dom_origin', 'variables_updated']
    if not method of proto
      throw new Error("Method #{method} required in Layoutable classes")

  _.extend proto, Layoutable

_constrainer = (op) ->
  () ->
    args = [null]
    for arg in arguments
      args.push(arg)
    new Constraint( new (Function.prototype.bind.apply(Expression, args)), op )

EQ = _constrainer(Operator.Eq)
GE = _constrainer(Operator.Ge)
LE = _constrainer(Operator.Le)

_weak_constrainer = (op) ->
  () ->
    args = [null]
    for arg in arguments
      args.push(arg)
    new Constraint( new (Function.prototype.bind.apply(Expression, args)), op, kiwi.Strength.weak )

WEAK_EQ = _weak_constrainer(Operator.Eq)
WEAK_GE = _weak_constrainer(Operator.Ge)
WEAK_LE = _weak_constrainer(Operator.Le)

module.exports =
  mixin_layoutable: mixin_layoutable,
  EQ: EQ,
  GE: GE,
  LE: LE,
  WEAK_EQ: WEAK_EQ,
  WEAK_GE: WEAK_GE,
  WEAK_LE: WEAK_LE
