#   use Industry_Statistics_Tool environment

from dash import Dash, html, dcc, Input, Output
import dash_leaflet as dl
import plotly.express as px
import pandas as pd
import geopandas as gpd
import os
from os import getcwd
from os.path import join
import plotly.express as px
from dash_extensions.javascript import arrow_function, assign
import json

#   allows code to determine the region type based on the tier5 selected --> used to access file path
from constants import region_type


#   tier5 geometries global variable
global tier5_data

#   tier5 geometries
tier5_data = gpd.read_file(join(getcwd(), 'service_areas', 'Tier5_Niveau5_May192020.TAB'))

#   tooltip of tier5 is service area name
tier5_data["tooltip"] = tier5_data.Service_Area_Name


#   initial region type selected in radio button is Rural-Remote
tier5_regions = os.listdir(join("industry_datasets", "Rural-Remote"))
tier5_industries = []

#   create geoJson layer of tier5 region
#   tier5 region fills in 'data' element
tier5_layer = dl.GeoJSON(hoverStyle=arrow_function(dict(weight=6, color = '#E11504')), id= 'tier5-map', options = dict(style ={'color' : '#E11504', 'fillOpacity' : 0}), zoomToBoundsOnClick= True)

app = Dash(__name__)

app.layout = html.Div(children=[
    #   title
    html.H1(children='Tier 5 Industry Statistics'),

    #   region type selector
    html.Label('select region type of interest'),
        dcc.RadioItems(id = 'region-type', options = ['Rural-Remote', 'Urban', 'Metro'], value = "Rural-Remote"),

    html.Br(),


    #   dropdown of tier5 regions, options are filled once region type has been selected
    html.Label('select tier5 of interest'),
        dcc.Dropdown(id = 'tier5', options = tier5_regions),

    html.Br(),

    #   ran out of time to implement as a dash Input
    #   display industry folders of chosen tier5 region
    #   desired function: when selected, display industry polygons on map
    html.Div([
    html.Label('select industries of interest'),
        dcc.Checklist(id = 'industries', options = tier5_industries),
    ], hidden = True, id = 'show-industries'),

    html.Br(),

    #   map layers -> map and tier5 geojson layer
    dl.Map([tier5_layer, dl.TileLayer()],
                center=[55.9995887, -97.6839348],
                zoom=4,
                style={
                    'width': '1000px',
                    'height': '500px'
                }, id = 'map'),


    #   display graphs of area distribution and industry count percentage
    html.Div([
        dcc.Graph(id="histogram"),
        dcc.Graph(id="pie"),
    ], hidden = True, id = 'show-statistics'),


   

    
])

#if region type is chosen, fill tier5 region options
@app.callback(
    Output('tier5', 'options'),
    Input('region-type', 'value'),
    
)

def choose_region_type(region_type):

    #read available tier5 datasets
    tier5_regions = os.listdir(join("industry_datasets", region_type))

    return  tier5_regions

#   if tier5 value is chosen, display region on map with statistics
@app.callback(
    Output('histogram', 'figure'),
    Output('pie', 'figure'),
    Output('show-statistics', 'hidden'),
    Output('industries', 'options'),
    Output('show-industries', 'hidden'),
    Output('tier5-map', 'data'),
    Output('map', 'zoom'),
    Output('map', 'center'),
    Input('tier5', 'value')
)

def display_tier5(tier5):

    #   read shp file containing all industry polygons
    all = gpd.read_file(join("industry_datasets", region_type[tier5], tier5, "_all", "gdf.shp"))

    #   create histogram of area distribution from industry polygons
    histogram = px.histogram(x = all['area']/1000000, title = 'Area Distribution', labels = {'x' : 'area km2'})

    all['count'] = 1

    #   create pie chart of industry counts 
    pie = px.pie(all, values='count', names='industry', title= 'Industry Count Percentage')
    
    
    #   read industry files and determine what industries exist in the tier5
    industries = os.listdir(join("industry_datasets", region_type[tier5], tier5))

    
    #   load tier5 geojson layer data with selected tier5
    #   identify by matching with Service Area Name attribute in TAB file. 
    #   TODO: some file names do not match the Service Area Name. ex. Montreal tier5 has a service area name of Island of Montreal 
    select_tier5 = tier5_data.loc[tier5_data["Service_Area_Name"] == tier5.replace("_", " ")]
    map_tier5 = json.loads(select_tier5.to_json())

    #   calculate center to zoom by identifying centroid
    lon,lat = list(select_tier5.geometry.item().centroid.coords)[0]
    center = [lat, lon]

    return histogram, pie, False, industries, False, map_tier5, 7, center

if __name__ == '__main__':
    app.run_server(debug=True)
