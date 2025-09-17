import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium
import branca

# Set the page layout to wide (full width)
st.set_page_config(layout="wide")

# Load data (assuming the data is in the same directory as the app.py file)
income = pd.read_csv(
    "https://raw.githubusercontent.com/pri-data/50-states/master/data/income-counties-states-national.csv",
    dtype={"fips": str},
)
income["income-2015"] = pd.to_numeric(income["income-2015"], errors="coerce")

# Calculate state-level median income
state_income_median = income.groupby("state").agg(
    medianincome_2015=("income-2015", "median"),
    medianincome_1989=("income-1989b", "median"), # Using income-1989b for consistent median calculation
    change=("change", "median"),
)

# Load state geometry data
import requests
import io
data = requests.get(
    "https://raw.githubusercontent.com/python-visualization/folium-example-data/main/us_states.json"
).json()

# Load state abbreviations
response = requests.get(
    "https://gist.githubusercontent.com/tvpmb/4734703/raw/b54d03154c339ed3047c66fefcece4727dfc931a/US%2520State%2520List"
).json()
abbrs = pd.DataFrame(response)

# Merge dataframes
states = geopandas.GeoDataFrame.from_features(data,crs="EPSG:4326")
statesmerge = states.merge(abbrs, how="inner", left_on="name", right_on="name")
statesmerge = statesmerge.merge(
    state_income_median,
    how="left",
    left_on="alpha-2",
    right_on="state",
)

# Build a color scale based on median income
colormap = branca.colormap.LinearColormap(
    vmin=statesmerge["medianincome_2015"].quantile(0.0),
    vmax=statesmerge["medianincome_2015"].quantile(1),
    colors=["red", "orange", "lightblue", "green", "darkgreen"],
    caption="State Level Median County Household Income in 2015 (USD)",
)

# Create a base map
income_map = folium.Map(location=[35.3, -97.6], zoom_start=4)

# Define what appears in click (popup) and hover (tooltip)
popup = folium.GeoJsonPopup(
    fields=["name", "medianincome_2015", "change"], # Fields/columns you want to display
    aliases=["State", "2015 Median Income (USD)", "% Change"], # Optional aliases you want to dispaly as field name instead of the keys for fields
    localize=True, # This is to format ‘clean’ values as strings i.e. 1,000,000.00 comma separators, float truncation, etc.
    labels=True, # display the field names or aliases
    style="background-color: yellow;", # HTML inline style properties like font and colors
)

tooltip = folium.GeoJsonTooltip(
    fields=["name", "medianincome_2015", "change"],
    aliases=["State:", "2015 Median Income(USD):", "Median % Change:"],
    localize=True,
    labels=True,
    style="""
        background-color: #F0EFEF;
        border: 2px solid black;
        border-radius: 3px;
        box-shadow: 3px;
    """,
    max_width=800,
)


# Add the GeoJson layer with style driven by the colormap
g = folium.GeoJson(
    statesmerge,
    style_function=lambda x: {
        "fillColor": colormap(x["properties"]["medianincome_2015"])
        if x["properties"]["medianincome_2015"] is not None
        else "transparent",
        "color": "black", # boundary color
        "fillOpacity": 0.6,
    },
    tooltip=tooltip,
    popup=popup,
).add_to(income_map)

colormap.add_to(income_map)


# Streamlit app layout
st.title("State Income Map through the US")

# Display the map
st_folium(income_map, height=600, width=1000)

# Add a dropdown to select a state
selected_state = st.selectbox("Select a State", statesmerge['name'].sort_values().unique())

# Filter data for the selected state
selected_state_income = income[income['state'] == statesmerge[statesmerge['name'] == selected_state]['alpha-2'].iloc[0]]

# Display county-level income data for the selected state
st.subheader(f"County Income Data for {selected_state}")
st.dataframe(selected_state_income[['county', 'income-2015', 'income-1989b']].dropna())

# Display state median income statistics
st.subheader(f"State Median Income Statistics for {selected_state}")
st.dataframe(state_income_median.loc[statesmerge[statesmerge['name'] == selected_state]['alpha-2'].iloc[0]])
