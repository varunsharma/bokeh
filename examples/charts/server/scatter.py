from bokeh.charts import interact, Scatter
import pandas as pd

data = {'a': [1, 2, 3, 4],
        'b': [3, 5, 4, 5],
        'c': ['foo', 'bar', 'foo', 'bar']}

interact(Scatter, pd.DataFrame(data), selectors=['x', 'y'])