""" Various kinds of layout components.

"""
from __future__ import absolute_import

import logging
logger = logging.getLogger(__name__)

from ..core import validation
from ..core.validation.warnings import EMPTY_LAYOUT, BOTH_CHILD_AND_ROOT  #noqa
from ..core.properties import abstract
from ..core.properties import Instance, List

from .component import Component


@abstract
class GridLayout(Component):
    """ Abstract base class for Row and Column. Do not use directly.
    """

    def __init__(self, *args, **kwargs):
        if len(args) > 0 and "children" in kwargs:
            raise ValueError("'children' keyword cannot be used with positional arguments")
        elif len(args) > 0:
            kwargs["children"] = list(args)
        super(GridLayout, self).__init__(**kwargs)

    @validation.warning(EMPTY_LAYOUT)
    def _check_empty_layout(self):
        from itertools import chain
        if not list(chain(self.children)):
            return str(self)

    @validation.warning(BOTH_CHILD_AND_ROOT)
    def _check_child_is_also_root(self):
        problems = []
        for c in self.children:
            if c.document is not None and c in c.document.roots:
                problems.append(str(c))
        if problems:
            return ", ".join(problems)
        else:
            return None

    children = List(Instance(Component), help="""
    The list of children, which can be other components including layouts,
    widgets and plots.
    """)


class Row(GridLayout):
    """ Lay out child components in a single horizontal row.

    Children can be specified as positional arguments, as a single argument
    that is a sequence, or using the ``children`` keyword argument.
    """


class Column(GridLayout):
    """ Lay out child components in a single vertical row.

    Children can be specified as positional arguments, as a single argument
    that is a sequence, or using the ``children`` keyword argument.
    """
