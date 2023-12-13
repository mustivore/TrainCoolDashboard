import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objs as go

df = pd.read_csv('anomalies.csv', sep=';')
df = df[df['mapped_veh_id'] == 103]
df['timestamps_UTC'] = pd.to_datetime(df['timestamps_UTC'])
df = df.sort_values('timestamps_UTC')

cols_pc1_split1 = ['RS_E_InAirTemp_PC1', 'RS_E_WatTemp_PC1', 'RS_T_OilTemp_PC1', 'speed']
cols_pc1_split2 = ['RS_E_OilPress_PC1', 'RS_E_RPM_PC1', 'speed']
cols_pc2_split1 = ['RS_E_InAirTemp_PC2', 'RS_E_WatTemp_PC2', 'RS_T_OilTemp_PC2', 'speed']
cols_pc2_split2 = ['RS_E_OilPress_PC2', 'RS_E_RPM_PC2', 'speed']
anomaly_columns = ['anomaly_RS_E_InAirTemp_PC1', 'anomaly_RS_T_OilTemp_PC1', 'anomaly_RS_E_OilPress_PC1',
                   'anomaly_RS_E_RPM_PC1', 'anomaly_RS_E_WatTemp_PC1']

date_min = df['timestamps_UTC'].min()
date_max = date_min + pd.DateOffset(1)
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
        start_date=date_min,
        end_date=date_max,
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

    fig = go.Figure()
    for col in cols_pc1_split1:
        # plot datas
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

    fig2 = px.line(filtered_data, x='timestamps_UTC', y=[col for col in cols_pc1_split2],
                   title=f"PC1")

    fig3 = px.line(filtered_data, x='timestamps_UTC', y=[col for col in cols_pc2_split1],
                   title=f"PC2")
    fig4 = px.line(filtered_data, x='timestamps_UTC', y=[col for col in cols_pc2_split2],
                   title=f"PC2")

    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(x=filtered_data['timestamps_UTC'], y=filtered_data['outside_temp'],
                              mode='markers', marker=dict(size=8, color=filtered_data['outside_temp'],
                                                          colorscale='Viridis', showscale=True),
                              name='Température extérieure'))
    fig5.update_layout(title=f"Température extérieure pour {selected_vehicule}",
                       xaxis_title='Timestamps',
                       yaxis_title='Température (°C)')

    fig_map = px.scatter_mapbox(filtered_data, lat='lat', lon='lon',
                                hover_name='mapped_veh_id', zoom=8)

    anomalies_present = filtered_data[anomaly_columns].apply(lambda row: 'Yes' in row.values, axis=1)

    anomalies = filtered_data[anomalies_present]
    if not anomalies.empty:
        fig_map.add_trace(go.Scattermapbox(
            lat=anomalies['lat'],
            lon=anomalies['lon'],
            mode='markers',
            marker=dict(size=10, color='red'),
            name='Anomalies'
        ))

    fig_map.update_layout(
        mapbox_style="open-street-map",
        title='Map',
    )

    fig_map.update_traces(
        customdata=filtered_data[['mapped_veh_id', 'timestamps_UTC']+anomaly_columns],
        hovertemplate="<b>%{customdata[0]}</b><br>Timestamp: %{customdata[1]}"
                      "<br>Anomalies: %{customdata[2]} %{customdata[3]} %{customdata[4]} "
                      "%{customdata[5]} %{customdata[6]}"
    )

    return [
        dcc.Graph(figure=fig),
        dcc.Graph(figure=fig3),
        dcc.Graph(figure=fig2),
        dcc.Graph(figure=fig4),
        dcc.Graph(figure=fig5),
        dcc.Graph(figure=fig_map)
    ]


if __name__ == '__main__':
    app.run_server(debug=True)
