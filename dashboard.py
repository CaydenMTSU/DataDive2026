import json
import urllib.request
import folium
import pandas as pd

# 1. Add your working Carto API key here
CARTO_API_KEY = "cb1_3yqq_1_51084aa0907c142f56a22eb5"

# 2. Extract and format your data frequencies perfectly 
county_counts = trimmed_data['COUNTYNAME'].value_counts().reset_index()
county_counts.columns = ['COUNTYNAME', 'Frequency']

# Force clean, consistent formatting to guarantee matches
county_counts['COUNTYNAME'] = (
    county_counts['COUNTYNAME']
    .str.replace(' County', '', case=False)
    .str.strip()
    .str.upper()
)

# Convert your counts into a dictionary for fast lookup when building tooltips
freq_dict = dict(zip(county_counts['COUNTYNAME'], county_counts['Frequency']))

# 3. USE A STABLE, TENNESSEE-ONLY GEOJSON FILE
# This completely limits the scope to TN and removes all out-of-state county lines
tn_geojson_url = "https://gist.githubusercontent.com/sdwfrost/d1c73f91dd9d175998ed166eb216994a/raw/e89c35f308cee7e2e5a784e1d3afc5d449e9e4bb/counties.geojson"

with urllib.request.urlopen(tn_geojson_url) as url:
    tn_geojson = json.loads(url.read().decode())

# Loop over the Tennessee-only counties to inject custom tooltip fields
for feature in tn_geojson['features']:
    # This specific file stores county names under 'name' (e.g., "Davidson")
    raw_name = feature['properties'].get('name', '')
    upper_name = str(raw_name).strip().upper()
    
    # Inject handshake keys and display metrics for the tooltip box
    feature['properties']['MATCH_NAME'] = upper_name
    feature['properties']['NAME_DISPLAY'] = upper_name.title()
    feature['properties']['FREQ_DISPLAY'] = int(freq_dict.get(upper_name, 0))

# 4. Initialize a base map layout centered squarely on Tennessee
tn_map = folium.Map(location=[35.75, -86.25], zoom_start=7, tiles=None)

# 5. Inject your custom background tile URL
custom_tile_url = f"https://cartocdn.com{{z}}/{{x}}/{{y}}.png?key={CARTO_API_KEY}"

folium.TileLayer(
    tiles=custom_tile_url,
    attr="&copy; <a href='https://openstreetmap.org'>OpenStreetMap</a> contributors &copy; <a href='https://carto.com'>CARTO</a>",
    name="Positron Base"
).add_to(tn_map)

# 6. Generate the Choropleth Data Layer (Handles the beautiful colors)
folium.Choropleth(
    geo_data=tn_geojson,                         
    name="choropleth",
    data=county_counts,                          
    columns=["COUNTYNAME", "Frequency"],         
    key_on="feature.properties.MATCH_NAME",   
    fill_color="YlOrRd",                         # Vibrant Yellow -> Orange -> Red heat ramp
    fill_opacity=0.8,                           
    line_opacity=0.6,                            
    line_color="white",                          # Crisp white county separator lines
    legend_name="Data Volume Frequency Count",
    highlight=True,                              
    nan_fill_color="#DCDCDC",                    # ASK 2 FIXED: Smooth, uniform soft gray (Gainsboro) for unrepresented counties
    nan_fill_opacity=0.6
).add_to(tn_map)

# 7. Create and inject the interactive Hover Tooltip layer
folium.GeoJson(
    tn_geojson,
    style_function=lambda x: {'fillOpacity': 0, 'weight': 0}, # Invisible capture layer for tracking mouse hovers
    tooltip=folium.GeoJsonTooltip(
        fields=['NAME_DISPLAY', 'FREQ_DISPLAY'],              
        aliases=['County Name:', 'Frequency Count:'],          
        localize=True,
        sticky=True,                                          
        labels=True,
        style="""
            background-color: #F0F2F6;
            border: 2px solid #31333F;
            border-radius: 4px;
            box-shadow: 3px 3px rgba(0,0,0,0.15);
            font-family: sans-serif;
            font-size: 13px;
            color: #31333F;
        """                                                   
    )
).add_to(tn_map)

# 8. Save out your refined map
tn_map.save("tn_county_heatmap.html")
print("Refined Tennessee map successfully saved as 'tn_county_heatmap.html'!")
