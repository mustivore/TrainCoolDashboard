import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

df = pd.read_csv('demo.csv', sep=';')
df['timestamps_UTC'] = pd.to_datetime(df['timestamps_UTC'])

cols_pc1_split1 = ['RS_E_InAirTemp_PC1', 'RS_E_WatTemp_PC1', 'RS_T_OilTemp_PC1', 'speed']
cols_pc1_split2 = ['RS_E_OilPress_PC1', 'RS_E_RPM_PC1', 'speed']
cols_pc2_split1 = ['RS_E_InAirTemp_PC2', 'RS_E_WatTemp_PC2', 'RS_T_OilTemp_PC2', 'speed']
cols_pc2_split2 = ['RS_E_OilPress_PC2', 'RS_E_RPM_PC2', 'speed']
anomaly_columns_pc1 = ['anomaly_RS_E_InAirTemp_PC1', 'anomaly_RS_T_OilTemp_PC1', 'anomaly_RS_E_OilPress_PC1',
                       'anomaly_RS_E_RPM_PC1', 'anomaly_RS_E_WatTemp_PC1']
anomaly_columns_pc2 = ['anomaly_RS_E_InAirTemp_PC2', 'anomaly_RS_T_OilTemp_PC2', 'anomaly_RS_E_OilPress_PC2',
                       'anomaly_RS_E_RPM_PC2', 'anomaly_RS_E_WatTemp_PC2']

date_min = df['timestamps_UTC'].min()
date_max = date_min + pd.DateOffset(1)
app = dash.Dash(__name__, suppress_callback_exceptions=True)
# app = dash.Dash(__name__, suppress_callback_exceptions=False)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),

    html.Div([
        dcc.Link('Home', href='/'),
        dcc.Link('Map', href='/map'),
    ]),

    html.Div(id='page-content')
])


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/map':
        layout = html.Div([
            html.Label("Choisir un véhicule :"),
            dcc.Dropdown(
                id='vehicule-dropdown',
                options=[{'label': 'All vehicles', 'value': 'all'}] +
                        [{'label': veh_id, 'value': veh_id} for veh_id in df['mapped_veh_id'].unique()],
                value=['all'],
                multi=True
            ),
            html.Label("Choisir une province :"),
            dcc.Dropdown(
                id='province-dropdown',
                options=[{'label': 'All provinces', 'value': 'all'}] +
                        [{'label': province, 'value': province} for province in df['province_name'].unique()],
                value='all'
            ),
            dcc.DatePickerRange(
                id='date-range-picker-map',
                start_date=date_min,
                end_date=date_max,
                display_format='YYYY-MM-DD',
            ),
            dcc.Graph(id='map-plot')
        ])
        return layout
    else:
        return html.Div([
            html.Label("Choisir un véhicule :"),
            dcc.Dropdown(
                id='vehicule-dropdown',
                options=[{'label': veh_id, 'value': veh_id} for veh_id in df['mapped_veh_id'].unique()],
                value=180
            ),
            html.Label("Choisir une période :"),
            dcc.DatePickerRange(
                id='date-range-picker',
                start_date=date_min,
                end_date=date_max,
                display_format='YYYY-MM-DD'
            ),
            html.Div(id='output-graphs')
        ])


@app.callback(
    Output('map-plot', 'figure'),
    [Input('vehicule-dropdown', 'value'),
     Input('province-dropdown', 'value'),
     Input('date-range-picker-map', 'start_date'),
     Input('date-range-picker-map', 'end_date')]
)
def update_map(selected_vehicules, selected_province, start_date, end_date):
    print(start_date, end_date)
    filtered_data = df[(df['timestamps_UTC'] >= start_date) & (df['timestamps_UTC'] <= end_date)]
    if 'all' not in selected_vehicules:
        filtered_data = df[df['mapped_veh_id'].isin(selected_vehicules)]

    if selected_province != 'all':
        filtered_data = filtered_data[filtered_data['province_name'] == selected_province]

    fig_map = go.Figure(go.Scattermapbox())
    fig_map.update_layout(mapbox_style="open-street-map", height=800)
    formatted_timestamps = filtered_data['timestamps_UTC'].dt.strftime('%Y-%m-%d %H:%M:%S')
    filtered_data = filtered_data.assign(formatted_timestamps=formatted_timestamps)
    anomalies_present = filtered_data[anomaly_columns_pc1 + anomaly_columns_pc2] \
        .apply(lambda row: 'Yes' in row.values, axis=1)
    anomalies_map = filtered_data[anomalies_present]
    not_anomalies_map = filtered_data[~anomalies_present]

    if not anomalies_map.empty:
        fig_map.add_trace(go.Scattermapbox(
            lat=anomalies_map['lat'],
            lon=anomalies_map['lon'],
            mode='markers',
            marker=dict(size=8, color='red'),
            customdata=anomalies_map[['mapped_veh_id', 'formatted_timestamps']
                                     + anomaly_columns_pc1 + anomaly_columns_pc2 + ['outside_temp']],
            hovertemplate="<b>%{customdata[0]}</b><br>Timestamp: %{customdata[1]}"
                          "<br>Outside temperature: %{customdata[12]}°C"
                          "<br>Anomalies PC1: RS_E_InAirTemp_PC1:%{customdata[2]} RS_T_OilTemp_PC1:%{customdata[3]} "
                          "RS_E_OilPress_PC1:%{customdata[4]} RS_E_RPM_PC1:%{customdata[5]} "
                          "RS_E_WatTemp_PC1:%{customdata[6]}"
                          "<br>Anomalies PC2: RS_E_InAirTemp_PC2:%{customdata[7]} RS_T_OilTemp_PC2:%{customdata[8]} "
                          "RS_E_OilPress_PC2:%{customdata[9]} RS_E_RPM_PC2:%{customdata[10]} "
                          "RS_E_WatTemp_PC2:%{customdata[11]}",
            name='Anomalies'
        ))

    if not not_anomalies_map.empty:
        fig_map.add_trace(go.Scattermapbox(
            lat=not_anomalies_map['lat'],
            lon=not_anomalies_map['lon'],
            mode='markers',
            marker=dict(size=8, color='blue'),
            customdata=not_anomalies_map[['mapped_veh_id', 'formatted_timestamps']
                                         + anomaly_columns_pc1 + anomaly_columns_pc2 + ['outside_temp']],
            hovertemplate="<b>%{customdata[0]}</b><br>Timestamp: %{customdata[1]}"
                          "<br>Outside temperature: %{customdata[12]}°C"
                          "<br>Anomalies PC1: RS_E_InAirTemp_PC1:%{customdata[2]} RS_T_OilTemp_PC1:%{customdata[3]} "
                          "RS_E_OilPress_PC1:%{customdata[4]} RS_E_RPM_PC1:%{customdata[5]} "
                          "RS_E_WatTemp_PC1:%{customdata[6]}"
                          "<br>Anomalies PC2: RS_E_InAirTemp_PC1:%{customdata[7]} RS_T_OilTemp_PC1:%{customdata[8]} "
                          "RS_E_OilPress_PC1:%{customdata[9]} RS_E_RPM_PC1:%{customdata[10]} "
                          "RS_E_WatTemp_PC1:%{customdata[11]}",
            name='Not anomalies'
        ))

    fig_map.update_layout(
        mapbox_style="open-street-map",
        title='trains',
        mapbox=dict(
            center=dict(lat=filtered_data['lat'].mean(), lon=filtered_data['lon'].mean()),
            zoom=8
        )
    )

    return fig_map


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
    filtered_data = filtered_data.sort_values('timestamps_UTC')
    fig = go.Figure()
    for col in cols_pc1_split1:
        # plot normal datas
        fig.add_trace(go.Scatter(
            x=filtered_data['timestamps_UTC'],
            y=filtered_data[col],
            mode='lines',
            name=col
        ))
        if col != 'speed':
            # plot anomalies
            anomalies = filtered_data.loc[filtered_data[f'anomaly_{col}'] == 'Yes', ['timestamps_UTC', col]]
            fig.add_trace(go.Scatter(
                x=anomalies['timestamps_UTC'],
                y=anomalies[col],
                mode='markers',
                marker=dict(color='red', size=8),
                name=f'Anomaly - {col}'
            ))
    fig.update_layout(title='PC1 sensor: RS_E_InAirTemp RS_E_WatTemp RS_T_OilTemp, speed')

    fig2 = go.Figure()
    for col in cols_pc1_split2:
        # plot datas
        fig2.add_trace(go.Scatter(
            x=filtered_data['timestamps_UTC'],
            y=filtered_data[col],
            mode='lines',
            name=col
        ))
        if col != 'speed':
            # plot anomalies
            anomalies = filtered_data.loc[filtered_data[f'anomaly_{col}'] == 'Yes', ['timestamps_UTC', col]]
            fig2.add_trace(go.Scatter(
                x=anomalies['timestamps_UTC'],
                y=anomalies[col],
                mode='markers',
                marker=dict(color='red', size=8),
                name=f'Anomaly - {col}'
            ))
    fig2.update_layout(title='PC1 sensor: RS_E_OilPress, RS_E_RPM, speed')

    fig3 = go.Figure()
    for col in cols_pc2_split1:
        # plot datas
        fig3.add_trace(go.Scatter(
            x=filtered_data['timestamps_UTC'],
            y=filtered_data[col],
            mode='lines',
            name=col
        ))
        if col != 'speed':
            # plot anomalies
            anomalies = filtered_data.loc[filtered_data[f'anomaly_{col}'] == 'Yes', ['timestamps_UTC', col]]
            fig3.add_trace(go.Scatter(
                x=anomalies['timestamps_UTC'],
                y=anomalies[col],
                mode='markers',
                marker=dict(color='red', size=8),
                name=f'Anomaly - {col}'
            ))
    fig3.update_layout(title='PC2 sensor: RS_E_InAirTemp RS_E_WatTemp RS_T_OilTemp, speed')

    fig4 = go.Figure()
    for col in cols_pc2_split2:
        # plot datas
        fig4.add_trace(go.Scatter(
            x=filtered_data['timestamps_UTC'],
            y=filtered_data[col],
            mode='lines',
            name=col
        ))
        if col != 'speed':
            # plot anomalies
            anomalies = filtered_data.loc[filtered_data[f'anomaly_{col}'] == 'Yes', ['timestamps_UTC', col]]
            fig4.add_trace(go.Scatter(
                x=anomalies['timestamps_UTC'],
                y=anomalies[col],
                mode='markers',
                marker=dict(color='red', size=8),
                name=f'Anomaly - {col}'
            ))
    fig4.update_layout(title='PC2 sensor: RS_E_OilPress, RS_E_RPM, speed')

    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(x=filtered_data['timestamps_UTC'], y=filtered_data['outside_temp'],
                              mode='markers', marker=dict(size=8, color=filtered_data['outside_temp'],
                                                          colorscale='Viridis', showscale=True),
                              name='Outside temperature'))
    fig5.update_layout(title=f"Outside temperature",
                       xaxis_title='Timestamps',
                       yaxis_title='Temperature (°C)')

    formatted_timestamps = filtered_data['timestamps_UTC'].dt.strftime('%Y-%m-%d %H:%M:%S')
    filtered_data = filtered_data.assign(formatted_timestamps=formatted_timestamps)
    fig_map = go.Figure(go.Scattermapbox())
    anomalies_present = filtered_data[anomaly_columns_pc1 + anomaly_columns_pc2] \
        .apply(lambda row: 'Yes' in row.values, axis=1)
    anomalies_map = filtered_data[anomalies_present]
    not_anomalies_map = filtered_data[~anomalies_present]
    if not anomalies_map.empty:
        fig_map.add_trace(go.Scattermapbox(
            lat=anomalies_map['lat'],
            lon=anomalies_map['lon'],
            mode='markers',
            marker=dict(size=8, color='red'),
            customdata=anomalies_map[['mapped_veh_id', 'formatted_timestamps']
                                     + anomaly_columns_pc1 + anomaly_columns_pc2 + ['outside_temp']],
            hovertemplate="<b>%{customdata[0]}</b><br>Timestamp: %{customdata[1]}"
                          "<br>Outside temperature: %{customdata[12]}°C"
                          "<br>Anomalies PC1: RS_E_InAirTemp_PC1:%{customdata[2]} RS_T_OilTemp_PC1:%{customdata[3]} "
                          "RS_E_OilPress_PC1:%{customdata[4]} RS_E_RPM_PC1:%{customdata[5]} "
                          "RS_E_WatTemp_PC1:%{customdata[6]}"
                          "<br>Anomalies PC2: RS_E_InAirTemp_PC2:%{customdata[7]} RS_T_OilTemp_PC2:%{customdata[8]} "
                          "RS_E_OilPress_PC2:%{customdata[9]} RS_E_RPM_PC2:%{customdata[10]} "
                          "RS_E_WatTemp_PC2:%{customdata[11]}",
            name='Anomalies'
        ))

    if not not_anomalies_map.empty:
        fig_map.add_trace(go.Scattermapbox(
            lat=not_anomalies_map['lat'],
            lon=not_anomalies_map['lon'],
            mode='markers',
            marker=dict(size=8, color='blue'),
            customdata=not_anomalies_map[['mapped_veh_id', 'formatted_timestamps']
                                         + anomaly_columns_pc1 + anomaly_columns_pc2 + ['outside_temp']],
            hovertemplate="<b>%{customdata[0]}</b><br>Timestamp: %{customdata[1]}"
                          "<br>Outside temperature: %{customdata[12]}°C",
            name='Not anomalies'
        ))

    fig_map.update_layout(
        mapbox_style="open-street-map",
        title="Train position",
        height=650,
        mapbox=dict(
            center=dict(lat=filtered_data['lat'].mean(), lon=filtered_data['lon'].mean()),
            zoom=8
        )
    )

    return [
        dcc.Graph(figure=fig),
        dcc.Graph(figure=fig2),
        dcc.Graph(figure=fig3),
        dcc.Graph(figure=fig4),
        dcc.Graph(figure=fig5),
        dcc.Graph(figure=fig_map)
    ]


if __name__ == '__main__':
    app.run_server(debug=True)
