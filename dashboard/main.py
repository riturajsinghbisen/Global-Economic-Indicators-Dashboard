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
df=load_data()
with st.expander("📊 Dataset Overview"):
    st.write(f"**Rows:** {df.shape[0]:,} &nbsp;&nbsp; **Columns:** {df.shape[1]}")
    st.write(f"**Countries covered:** {df['Country Name'].nunique()} &nbsp;&nbsp; "
             f"**Years:** {int(df['Year'].min())}–{int(df['Year'].max())}")
    overview = pd.DataFrame({
        "Column": df.columns,
        "Data Type": df.dtypes.astype(str).values,
        "Missing Values": df.isna().sum().values,
    })
    st.dataframe(overview, use_container_width=True, hide_index=True)
    st.caption("First 5 rows:")
    st.dataframe(df.head(), use_container_width=True)
# Human-readable number formatting for KPI cards (e.g. $2.40B instead of $2,400,000,000)
def human_number(n, prefix=""):
    if pd.isna(n):
        return "N/A"
    abs_n = abs(n)
    for unit, div in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs_n >= div:
            return f"{prefix}{n / div:,.2f}{unit}"
    return f"{prefix}{n:,.0f}"
# Sidebar — Filters
st.sidebar.header("Filters")

if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

if st.sidebar.button("↺ Reset filters"):
    st.session_state.reset_counter += 1
    st.rerun()

fk = st.session_state.reset_counter  # suffix added to widget keys so reset always starts fresh
# Filter 1: Continent (multi-select)
continents = sorted(df["Continent"].unique())
selected_continents = st.sidebar.multiselect(
    "Continent", options=continents, default=continents, key=f"continent_filter_{fk}"
)
# Narrow the country list down based on continent selection
countries_available = sorted(
    df[df["Continent"].isin(selected_continents)]["Country Name"].unique()
)
# Filter 2: Country (multi-select, defaults to a handful so charts aren't overcrowded)
default_countries = [c for c in ["India", "United States", "China", "Germany", "Brazil"]
                      if c in countries_available] or countries_available[:5]
selected_countries = st.sidebar.multiselect(
    "Country", options=countries_available, default=default_countries, key=f"country_filter_{fk}"
)
# Filter 3: Year range (slider)
min_year, max_year = int(df["Year"].min()), int(df["Year"].max())
year_range = st.sidebar.slider(
    "Year range", min_value=min_year, max_value=max_year,
    value=(2010, max_year), step=1, key=f"year_filter_{fk}"
)
st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ About this dashboard"):
    st.write(
        "Data: World Bank indicators (GDP, Population, Inflation), 2000–2022, "
        "212 countries. Sourced via the community-maintained "
        "[datasets](https://github.com/datasets) GitHub organization "
        "(original data from the World Bank)."
    )
# Apply filters
mask = (
    df["Continent"].isin(selected_continents)
    & df["Country Name"].isin(selected_countries)
    & df["Year"].between(year_range[0], year_range[1])
)
filtered = df[mask]
st.title("Global Economic Indicators Dashboard")
st.caption("Design and build an interactive dashboard for dynamic data visualization and filtering of datasets.")
if filtered.empty:
    st.warning("No data matches the current filters. Try widening your selection.")
    st.stop()
# KPI cards — based on the most recent year within the selected range
latest_year = filtered["Year"].max()
latest = filtered[filtered["Year"] == latest_year]
prev = filtered[filtered["Year"] == latest_year - 1]

avg_gdp_per_capita = latest["GDP_per_capita_USD"].mean()
avg_inflation = latest["Inflation_Pct"].mean()
total_population = latest["Population"].sum()

prev_gdp_per_capita = prev["GDP_per_capita_USD"].mean() if not prev.empty else None
prev_inflation = prev["Inflation_Pct"].mean() if not prev.empty else None
prev_population = prev["Population"].sum() if not prev.empty else None

def pct_delta(curr, prev):
    if prev in (None, 0) or pd.isna(prev) or pd.isna(curr):
        return None
    return f"{(curr - prev) / prev * 100:+.1f}%"

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(
    f"Avg GDP per Capita ({latest_year})",
    human_number(avg_gdp_per_capita, "$"),
    delta=pct_delta(avg_gdp_per_capita, prev_gdp_per_capita),
)
kpi2.metric(
    f"Avg Inflation % ({latest_year})",
    f"{avg_inflation:.2f}%" if pd.notna(avg_inflation) else "N/A",
    delta=pct_delta(avg_inflation, prev_inflation),
    delta_color="inverse",
)
kpi3.metric(
    f"Total Population ({latest_year})",
    human_number(total_population),
    delta=pct_delta(total_population, prev_population),
)
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