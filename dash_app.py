import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
import sqlite3

# Sample sales data
def get_sales_data():
    conn = sqlite3.connect('database.db')

    # Query to fetch sales data
    query = "SELECT Date, TotalPrice FROM sales_table ORDER BY Date"

    # Read the data into DataFrame
    df = pd.read_sql_query(query, conn)
    conn.close()

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])

    return df

def get_sales_trend_figure(df):
    daily_sales = df.groupby('Date')['TotalPrice'].sum().reset_index()

    fig = px.line(daily_sales, x='Date', y='TotalPrice',
            title="Daily Sales Trend",
            labels={"Date": "Date", "TotalPrice": "Total Sales (NRP)"})

    fig.update_layout(
            title="Daily Sales Trend",
            xaxis_title="Date",
            yaxis_title="Total Sales (NRP)",
            template="plotly_white",
            autosize=True,
            margin=dict(l=30, r=30, t=60, b=40),
            )

    return fig

def create_dash_app():
    app = dash.Dash(__name__, requests_pathname_prefix='/dash/')

    df = get_sales_data()

    trend_fig = get_sales_trend_figure(df)

    app.layout = html.Div([
        html.H2("Sales Dashboard"),
        html.Div([
            html.H4("Sales Trend"),
            dcc.Graph(figure=trend_fig)
            ])
        ])

    return app

