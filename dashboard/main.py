"""
Global Economic Indicators Dashboard
Filters   : Continent, Country, Year range
KPIs      : Avg GDP per capita, Avg Inflation %, Total Population (for current selection)
Charts    : Line (trend over years), Choropleth map (by country), Bar (top N by GDP per capita)
"""
import pandas as pd
import plotly.express as px
import streamlit as st
# Page config
st.set_page_config(
    page_title="Global Economic Indicators",
    page_icon="🌍",
    layout="wide",
)

# Data loading (cached so it doesn't reload on every filter interaction)
import os
@st.cache_data
def load_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "global_economic_indicators.csv")
    return pd.read_csv(csv_path)

# Sidebar — Filters
st.sidebar.header("Filters")
# Filter 1: Continent (multi-select)
continents = sorted(df["Continent"].unique())
selected_continents = st.sidebar.multiselect(
    "Continent", options=continents, default=continents
)
# Narrow the country list down based on continent selection
countries_available = sorted(
    df[df["Continent"].isin(selected_continents)]["Country Name"].unique()
)
# Filter 2: Country (multi-select, defaults to a handful so charts aren't overcrowded)
default_countries = [c for c in ["India", "United States", "China", "Germany", "Brazil"]
                      if c in countries_available] or countries_available[:5]
selected_countries = st.sidebar.multiselect(
    "Country", options=countries_available, default=default_countries
)
# Filter 3: Year range (slider)
min_year, max_year = int(df["Year"].min()), int(df["Year"].max())
year_range = st.sidebar.slider(
    "Year range", min_value=min_year, max_value=max_year,
    value=(2010, max_year), step=1
)
st.sidebar.markdown("---")
st.sidebar.caption(
    "Data: World Bank (GDP, Population, Inflation), 2000–2022. "
    "Sourced via github.com/datasets."
)
# Apply filters
mask = (
    df["Continent"].isin(selected_continents)
    & df["Country Name"].isin(selected_countries)
    & df["Year"].between(year_range[0], year_range[1])
)
filtered = df[mask]
st.title("🌍 Global Economic Indicators Dashboard")
st.caption("Design and build an interactive dashboard for dynamic data visualization and filtering of datasets.")
if filtered.empty:
    st.warning("No data matches the current filters. Try widening your selection.")
    st.stop()
# KPI cards — based on the most recent year within the selected range
latest_year = filtered["Year"].max()
latest = filtered[filtered["Year"] == latest_year]
avg_gdp_per_capita = latest["GDP_per_capita_USD"].mean()
avg_inflation = latest["Inflation_Pct"].mean()
total_population = latest["Population"].sum()
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(f"Avg GDP per Capita ({latest_year})", f"${avg_gdp_per_capita:,.0f}")
kpi2.metric(f"Avg Inflation % ({latest_year})",
            f"{avg_inflation:.2f}%" if pd.notna(avg_inflation) else "N/A")
kpi3.metric(f"Total Population ({latest_year})", f"{total_population:,.0f}")
st.markdown("---")
# Visualization 1: Line chart — GDP per capita trend over years
st.subheader("GDP per Capita Over Time")
fig_line = px.line(
    filtered.sort_values("Year"),
    x="Year", y="GDP_per_capita_USD", color="Country Name",
    markers=True,
    labels={"GDP_per_capita_USD": "GDP per Capita (US$)"},
)
st.plotly_chart(fig_line, use_container_width=True)
# Visualization 2: Choropleth map — GDP per capita by country, most recent year
st.subheader(f"GDP per Capita by Country ({latest_year})")
fig_map = px.choropleth(
    latest,
    locations="Country Code", color="GDP_per_capita_USD",
    hover_name="Country Name",
    color_continuous_scale="Viridis",
    labels={"GDP_per_capita_USD": "GDP per Capita (US$)"},
)
st.plotly_chart(fig_map, use_container_width=True)
# Visualization 3: Bar chart — top countries by GDP per capita, most recent year
st.subheader(f"Top Countries by GDP per Capita ({latest_year})")
top_n = latest.sort_values("GDP_per_capita_USD", ascending=False).head(10)
fig_bar = px.bar(
    top_n,
    x="Country Name", y="GDP_per_capita_USD", color="Continent",
    labels={"GDP_per_capita_USD": "GDP per Capita (US$)"},
)
st.plotly_chart(fig_bar, use_container_width=True)
# Raw data (optional, collapsible)
with st.expander("View filtered raw data"):
    st.dataframe(filtered.reset_index(drop=True))