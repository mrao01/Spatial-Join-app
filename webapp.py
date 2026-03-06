import streamlit as st
import pandas as pd
import geopandas as gpd
import requests
from shapely.geometry import Point

st.set_page_config(page_title="Spatial Join Tool", layout="wide")

st.title("📍 Spatial Attribute Appender")
st.markdown("Upload points (CSV/XLS), connect to a Polygon REST API, and download the results.")

# 1. Inputs
with st.sidebar:
    st.header("Settings")
    api_url = st.text_input("Polygon REST API URL", "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/USA_Counties_Generalized_Boundaries/FeatureServer/0/query")
    uploaded_file = st.file_uploader("Upload Points", type=["csv", "xlsx", "xls"])

if uploaded_file:
    # Handle File Type
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Data Preview", df.head(5))
        lon_col = st.selectbox("Select Longitude Column (X)", df.columns)
        lat_col = st.selectbox("Select Latitude Column (Y)", df.columns)

    # 2. Map Preview (Pre-processing)
    with col2:
        st.write("### Point Preview")
        map_df = df[[lat_col, lon_col]].dropna()
        map_df.columns = ['lat', 'lon']
        st.map(map_df)

    if st.button("🚀 Process Spatial Join"):
        with st.spinner("Fetching polygons and intersecting..."):
            try:
                # 3. Create GeoDataFrame from Points
                gdf_points = gpd.GeoDataFrame(
                    df, geometry=gpd.points_from_xy(df[lon_col], df[lat_col]), crs="EPSG:4326"
                )

                # 4. Fetch Polygons from API
                params = {'where': '1=1', 'outFields': '*', 'f': 'geojson'}
                response = requests.get(api_url, params=params)
                gdf_polygons = gpd.read_file(response.text)

                # Ensure CRS match
                if gdf_polygons.crs != gdf_points.crs:
                    gdf_polygons = gdf_polygons.to_crs(gdf_points.crs)

                # 5. Spatial Join
                result = gpd.sjoin(gdf_points, gdf_polygons, how="left", predicate="within")

                # Clean up columns for the user
                final_df = result.drop(columns=['geometry', 'index_right'])
                
                st.divider()
                st.success(f"Done! {len(final_df)} points processed.")
                st.write("### Results Preview", final_df.head())
                
                # 6. Download
                csv_output = final_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Joined CSV", csv_output, "spatial_results.csv", "text/csv")
                
            except Exception as e:
                st.error(f"Error during processing: {e}")