import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objs as go


df = pd.read_csv('veh182.csv', sep=';')
df['timestamps_UTC'] = pd.to_datetime(df['timestamps_UTC'])
df = df.sort_values('timestamps_UTC')
app = dash.Dash(__name__)

app.layout = html.Div([
    html.Label("Choisir un véhicule :"),
    dcc.Dropdown(
        id='vehicule-dropdown',
        options=[{'label': veh_id, 'value': veh_id} for veh_id in df['mapped_veh_id'].unique()],
        value=df['mapped_veh_id'].unique()[0]
    ),
    html.Label("Choisir une période :"),
    dcc.DatePickerRange(
        id='date-range-picker',
        start_date=df['timestamps_UTC'].min(),
        end_date=df['timestamps_UTC'].max(),
        display_format='YYYY-MM-DD'
    ),
    html.Div(id='output-graphs')
])


@app.callback(
    Output('output-graphs', 'children'),
    [Input('vehicule-dropdown', 'value'),
     Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date')]
)
def update_graph(selected_vehicule, start_date, end_date):
    filtered_data = df[(df['mapped_veh_id'] == selected_vehicule) &
                       (df['timestamps_UTC'] >= start_date) &
                       (df['timestamps_UTC'] <= end_date)]

    fig1 = px.line(filtered_data, x='timestamps_UTC', y=[col for col in df.columns if 'PC1' in col],
                   title=f"Graphique pour {selected_vehicule} - PC1")
    fig2 = px.line(filtered_data, x='timestamps_UTC', y=[col for col in df.columns if 'PC2' in col],
                   title=f"Graphique pour {selected_vehicule} - PC2")

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=filtered_data['timestamps_UTC'], y=filtered_data['outside_temp'],
                              mode='markers', marker=dict(size=8, color=filtered_data['outside_temp'],
                                                          colorscale='Viridis', showscale=True),
                              name='Température extérieure'))
    fig3.update_layout(title=f"Température extérieure pour {selected_vehicule}",
                       xaxis_title='Timestamps',
                       yaxis_title='Température (°C)')

    fig_map = px.scatter_mapbox(filtered_data, lat='lat', lon='lon',
                                hover_name='mapped_veh_id', zoom=8)
    fig_map.update_layout(mapbox_style="open-street-map")

    return [
        dcc.Graph(figure=fig1),
        dcc.Graph(figure=fig2),
        dcc.Graph(figure=fig3),
        dcc.Graph(figure=fig_map)
    ]


if __name__ == '__main__':
    app.run_server(debug=True)
