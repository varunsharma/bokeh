import pandas as pd
import geopandas as gpd
from cartogram_geopandas import make_cartogram

import pdb
from bokeh.palettes import Spectral5
from bokeh.models import GeoJSONDataSource
from bokeh.plotting import Figure, show, output_file

counties_geojson = '/Users/bcollins/us_counties_lambert.geojson'
counties = gpd.read_file(counties_geojson)
counties.set_index('GEOID', inplace=True)

pop_csv = '/Users/bcollins/Downloads/PEP_2012_PEPANNRES/PEP_2012_PEPANNRES_with_ann.csv'
pop_df = pd.read_csv(pop_csv, encoding="ISO-8859-1")
pop_field = 'respop72012'
pop_df['GEOID'] = pop_df.apply(lambda r:str(r['id2']).zfill(5), axis=1)
pop_df.set_index('GEOID', inplace=True)

pop_counties = counties.join(pop_df, lsuffix='_bbb')
pop_sum = pop_counties[pop_field].sum()
pop_counties['pop_normalized'] = pop_counties.apply(lambda r:(r[pop_field] / pop_sum) * 100000000, axis=1)

counties['pop_norm'] = pop_counties['pop_normalized']

colors = list(reversed(Spectral5))
groups = pd.qcut(counties['pop_norm'].tolist(), len(colors))
counties['colors'] = [colors[l] for l in groups.codes]

percentiles = pd.qcut(counties['pop_norm'].tolist(), 100)
counties['pop_percentile'] = [l + 2 for l in percentiles.codes]

new = make_cartogram(counties, 'pop_percentile', 7, inplace=False)
geo_source = GeoJSONDataSource(geojson=new.to_json())
bounds = counties.total_bounds

p = Figure(plot_height=900, plot_width=1200,
           x_range=(bounds[0], bounds[2]),
           y_range=(bounds[1], bounds[3]),
           tools='pan,wheel_zoom')
p.axis.visible = False
p.grid.grid_line_alpha = 0

p.background_fill = "black"
p.patches(xs='xs', ys='ys',alpha=.8, source=geo_source, line_alpha=.2, line_color='#ffffff', color='colors')
output_file('cartogram_example.html')
show(p)
