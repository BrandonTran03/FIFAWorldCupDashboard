# Render link: 

import pandas as pd
import requests
from bs4 import BeautifulSoup
import dash
from dash import dcc, html, Input, Output
import plotly.express as px

response = requests.get("https://en.wikipedia.org/wiki/List_of_FIFA_World_Cup_finals")
soup = BeautifulSoup(response.text, "html.parser")

tables = soup.find_all("table", {"class": "wikitable"})
finals_table = None

for table in tables:
    caption = table.find("caption")
    if caption and "List of FIFA World Cup finals" in caption.text:
        finals_table = table
        break

if finals_table is None:
    print("Could not find the correct table.")
    exit()

rows = finals_table.find_all("tr")

# Extract headers
headers = [th.text.strip() for th in rows[0].find_all("th")]
data = []

for row in rows[1:]:
    cols = [td.text.strip() for td in row.find_all(["th", "td"])]
    if len(cols) >= 7:
        year = cols[0]
        winner = cols[1]
        runner_up = cols[3]
        data.append([year, winner, runner_up])

# Convert to DataFrame
df = pd.DataFrame(data, columns=["Year", "Winner", "Runner-Up"])

# Make West Germany and Germany the same
df.replace({"West Germany": "Germany"}, inplace=True)

# Calculate the number of wins per country
win_counts = df['Winner'].value_counts().reset_index()
win_counts.columns = ['Country', 'Wins']

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("FIFA Soccer World Cup Dashboard"),
    dcc.Graph(id="choropleth-map"),
    dcc.Dropdown(id="country-dropdown",
                 options=[{"label": country, "value": country} for country in sorted(df["Winner"].unique())],
                 placeholder="Select World Cup winner"),
    html.Div(id="country-wins"),
    dcc.Dropdown(id="year-dropdown",
                 options=[{"label": year, "value": year} for year in sorted(df["Year"].unique())],
                 placeholder="Select World Cup year"),
    html.Div(id="final-result"),
], style={'background-color': 'white'})

@app.callback(
    Output("choropleth-map", "figure"),
    Input("country-dropdown", "value")
)
def update_map(selected_country):
    fig = px.choropleth(
        win_counts,
        locations="Country",
        locationmode="country names",
        color="Wins",
        hover_name="Country",
        color_continuous_scale="Blues",
        title="World Cup Wins by Country"
    )
    return fig


@app.callback(
    Output("country-wins", "children"),
    Input("country-dropdown", "value")
)
def update_country_wins(selected_country):
    if selected_country:
        wins = len(df[df["Winner"] == selected_country])
        return f"{selected_country} has won the World Cup {wins} time(s)."
    return ""

@app.callback(
    Output("final-result", "children"),
    Input("year-dropdown", "value")
)
def update_final_result(selected_year):
    if selected_year:
        match = df[df["Year"] == selected_year]
        if not match.empty:
            winner = match["Winner"].values[0]
            runner_up = match["Runner-Up"].values[0]
            return f"1930 -> Winner = {winner}, Runner-up = {runner_up}"
    return ""

if __name__ == "__main__":
    app.run_server(debug=False)
