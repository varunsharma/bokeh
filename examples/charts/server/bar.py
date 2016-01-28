from bokeh.charts import interact, Bar
import pandas as pd

data = {'a': [1, 2, 3, 4],
        'b': [3, 5, 4, 5],
        'c': ['foo', 'bar', 'foo', 'bar']}

interact(Bar, pd.DataFrame(data), selectors=['values', 'label'], tooltips=[(
    'value', '@height')])