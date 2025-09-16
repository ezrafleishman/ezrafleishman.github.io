# Santa Cruz BCycle Dashboard

import requests
import pandas as pd
from dash import Dash, html, dcc, dash_table
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from IPython.display import display, HTML

# Fetch BCycle data

def fetch_bcycle_data():
    gbfs_url = 'https://gbfs.bcycle.com/bcycle_santacruz/gbfs.json'
    gbfs_data = requests.get(gbfs_url).json()
    
    feeds = gbfs_data['data']['en']['feeds']
    station_info_url = next(feed['url'] for feed in feeds if feed['name']=='station_information')
    station_status_url = next(feed['url'] for feed in feeds if feed['name']=='station_status')
    
    station_info = pd.DataFrame(requests.get(station_info_url).json()['data']['stations'])
    station_status = pd.DataFrame(requests.get(station_status_url).json()['data']['stations'])
    
    df = pd.merge(station_info, station_status, on='station_id')
    
    # Ensure numeric
    df['num_bikes_available'] = pd.to_numeric(df['num_bikes_available'], errors='coerce').fillna(0)
    df['num_docks_available'] = pd.to_numeric(df['num_docks_available'], errors='coerce').fillna(0)
    
    return df

# Dash Table helper

def generate_dash_table(df):
    return dash_table.DataTable(
        id='station-table',
        columns=[
            {'name':'Station Name','id':'name','type':'text'},
            {'name':'Bikes Available','id':'num_bikes_available','type':'numeric'},
            {'name':'Docks Available','id':'num_docks_available','type':'numeric'}
        ],
        data=df.to_dict('records'),
        sort_action='native',
        style_table={'overflowX':'auto'},
        style_header={
            'font-family':'Aptos',
            'textAlign':'center',
            'fontWeight':'bold',
            'fontSize':'16px'
        },
        style_cell={
            'font-family':'Aptos',
            'textAlign':'center',
            'fontSize':'14px',
        }
    )

# ------------------------
# Dash App
# ------------------------
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Santa Cruz BCycle Dashboard", 
            style={'textAlign':'center','fontWeight':'bold','fontFamily':'Aptos'}),
    
    html.Div(id='kpi-div', style={'margin-bottom':'20px','textAlign':'center','font-family':'Aptos','fontSize':'16px'}),
    
    dcc.Graph(id='map-graph'),
    
    html.H3("Available Station Details", 
            style={'textAlign':'center','fontWeight':'bold','fontSize':'20px','fontFamily':'Aptos'}),
    html.Div(id='table-div'),
    
    dcc.Interval(id='interval-component', interval=60*1000, n_intervals=0)
])

# ------------------------
# Callback
# ------------------------
@app.callback(
    Output('map-graph','figure'),
    Output('kpi-div','children'),
    Output('table-div','children'),
    Input('interval-component','n_intervals')
)
def update_dashboard(n):
    try:
        df = fetch_bcycle_data()
        
        # KPIs
        total_bikes = df['num_bikes_available'].sum()
        total_docks = df['num_docks_available'].sum()
        empty_stations = (df['num_bikes_available']==0).sum()
        full_stations = (df['num_docks_available']==0).sum()
        online_stations = len(df)
        
        kpi_layout = html.Div([
            html.Span(f"Total Bikes: {total_bikes}", style={'margin-right':'20px'}),
            html.Span(f"Total Docks: {total_docks}", style={'margin-right':'20px'}),
            html.Span(f"Empty Stations: {empty_stations}", style={'margin-right':'20px'}),
            html.Span(f"Full Stations: {full_stations}", style={'margin-right':'20px'}),
            html.Span(f"Stations Online: {online_stations}")
        ])
        
        # Center map
        map_center = {"lat": df['lat'].mean(), "lon": df['lon'].mean()}
        
        # Scattermapbox with uniform blue dots
        trace = go.Scattermapbox(
            lat=df['lat'],
            lon=df['lon'],
            mode='markers+text',
            text=df['num_bikes_available'].astype(str),
            textposition='top center',
            hoverinfo='text',
            hovertext=df.apply(lambda r: f"{r['name']}<br>Bikes: {r['num_bikes_available']}<br>Docks: {r['num_docks_available']}", axis=1),
            marker=dict(size=20, color='blue', opacity=0.9)
        )
        
        fig = go.Figure(trace)
        fig.update_layout(
            mapbox=dict(style="open-street-map", center=map_center, zoom=13),
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        
        # Table
        table_df = df[['name','num_bikes_available','num_docks_available']].copy()
        table = generate_dash_table(table_df)
        
        return fig, kpi_layout, table
    
    except Exception as e:
        return {}, html.Div(f"Error fetching data: {e}"), html.Div()

# ------------------------
# Run App, Update #LOCALPORT# to a local port you can use to execute dashboard
# ------------------------
if __name__ == '__main__':
    port = #LOCALPORT#
    url = f"#LOCALPORT#:{port}"
    display(HTML(f'<a href="{url}" target="_blank">Open Santa Cruz BCycle Dashboard</a>'))
    app.run(debug=True, port=port)
