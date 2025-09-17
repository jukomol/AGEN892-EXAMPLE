import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium
import branca
import geopandas
import requests



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
st.title("🗺️ State Income Map through the US")

# Add some custom CSS for beautification
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E8B57;
        font-size: 2.5rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .income-stats {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 4px solid #2E8B57;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .dropdown-container {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        margin: 2rem 0;
        border: 1px solid #e9ecef;
    }
    .top-states {
        background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin: 0.5rem 0;
    }
    .bottom-states {
        background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #e74c3c;
        margin: 0.5rem 0;
    }
    .state-rank {
        font-weight: bold;
        color: #2E8B57;
    }
    .income-value {
        color: #495057;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Create two-column layout for map and median income
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📍 Interactive Income Map")
    # Display the map
    st_folium(income_map, height=600, width=700)

with col2:
    st.subheader("💰 State Median Income Overview")
    
    # Calculate and display some key statistics
    median_income_stats = state_income_median['medianincome_2015'].describe()
    
    st.markdown('<div class="income-stats">', unsafe_allow_html=True)
    st.metric("Highest State Median Income", 
              f"${median_income_stats['max']:,.0f}",
              help="Highest median income among all states")
    st.metric("Lowest State Median Income", 
              f"${median_income_stats['min']:,.0f}",
              help="Lowest median income among all states")
    st.metric("National Average", 
              f"${median_income_stats['mean']:,.0f}",
              help="Average median income across all states")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Top 5 and Bottom 5 states
    top_states = state_income_median.nlargest(5, 'medianincome_2015')
    bottom_states = state_income_median.nsmallest(5, 'medianincome_2015')
    
    st.markdown('<div class="top-states">', unsafe_allow_html=True)
    st.subheader("🏆 Top 5 States by Median Income")
    for idx, (state, data) in enumerate(top_states.iterrows(), 1):
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "🏅"
        state_name = statesmerge[statesmerge['alpha-2'] == state]['name'].iloc[0] if not statesmerge[statesmerge['alpha-2'] == state].empty else state
        st.markdown(f"{medal} **{idx}. {state_name}**: <span class='income-value'>${data['medianincome_2015']:,.0f}</span>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="bottom-states">', unsafe_allow_html=True)
    st.subheader("📊 Bottom 5 States by Median Income")
    for idx, (state, data) in enumerate(bottom_states.iterrows(), 1):
        state_name = statesmerge[statesmerge['alpha-2'] == state]['name'].iloc[0] if not statesmerge[statesmerge['alpha-2'] == state].empty else state
        st.markdown(f"📉 **{idx}. {state_name}**: <span class='income-value'>${data['medianincome_2015']:,.0f}</span>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# State selection and detailed data section
st.markdown("---")
st.markdown('<div class="dropdown-container">', unsafe_allow_html=True)

col3, col4 = st.columns([1, 1])

with col3:
    st.subheader("🔍 Select a State for Detailed Analysis")
    selected_state = st.selectbox("Choose a State:", statesmerge['name'].sort_values().unique(), 
                                  help="Select a state to view detailed county-level income data")

with col4:
    if selected_state:
        state_code = statesmerge[statesmerge['name'] == selected_state]['alpha-2'].iloc[0]
        state_data = state_income_median.loc[state_code]
        
        st.subheader(f"📈 {selected_state} Quick Stats")
        st.metric("Median Income 2015", f"${state_data['medianincome_2015']:,.0f}")
        st.metric("Median Income 1989", f"${state_data['medianincome_1989']:,.0f}")
        st.metric("Income Change %", f"{state_data['change']:.1f}%")

st.markdown('</div>', unsafe_allow_html=True)

# Filter data for the selected state
selected_state_income = income[income['state'] == statesmerge[statesmerge['name'] == selected_state]['alpha-2'].iloc[0]]

# Display county-level income data for the selected state
st.subheader(f"🏘️ County Income Data for {selected_state}")
county_data = selected_state_income[['county', 'income-2015', 'income-1989b', 'change']].dropna()
county_data = county_data.sort_values('income-2015', ascending=False)

# Add some formatting to the dataframe
county_data_formatted = county_data.copy()
county_data_formatted['income-2015'] = county_data_formatted['income-2015'].apply(lambda x: f"${x:,.0f}")
county_data_formatted['income-1989b'] = county_data_formatted['income-1989b'].apply(lambda x: f"${x:,.0f}")
county_data_formatted['change'] = county_data_formatted['change'].apply(lambda x: f"{x:.1f}%")

st.dataframe(county_data_formatted, 
             column_config={
                 "county": "County",
                 "income-2015": "2015 Income",
                 "income-1989b": "1989 Income", 
                 "change": "Change %"
             },
             use_container_width=True)
