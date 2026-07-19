import streamlit as st
import requests
import pandas as pd

# Set up page configurations
st.set_page_config(page_title="LeadPulse - B2B Lead Extraper", page_icon="🧲", layout="wide")

st.title("🧲 LeadPulse - HyperLocal Business Lead Scraper")
st.markdown("Extract fresh, targeted local business leads directly into a clean spreadsheet in seconds.")

# Sidebar documentation block
st.sidebar.header("How it Works")
st.sidebar.markdown("""
1. Enter your target industry **Keyword**.
2. Specify the target **Location** (City/Region).
3. Select the data size depth using the **Limit Slider**.
4. Click **Extract Leads** and download your clean CSV spreadsheet.
""")

# Setup visual input structures
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    keyword = st.text_input("Business Type / Niche", placeholder="e.g., plumbers, dentists, hotels")
with col2:
    location = st.text_input("Target Location", placeholder="e.g., Nairobi, Mombasa, London")
with col3:
    limit = st.slider("Max Results Limit", min_value=10, max_value=100, value=20, step=10)

# Execution Action Trigger
if st.button("🚀 Extract Live Leads", use_container_width=True):
    if not keyword or not location:
        st.error("Please fill in both the Keyword and Location fields to initiate search protocols.")
    else:
        with st.spinner("Querying serverless pipelines and cleaning data indices... Please wait..."):
            # Target your live Vercel deployment link directly
            VERCEL_API_URL = "https://vercel.app"
            params = {
                "keyword": keyword,
                "location": location,
                "limit": limit
            }
            
            try:
                response = requests.get(VERCEL_API_URL, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    leads_list = data.get("leads", [])
                    
                    if not leads_list:
                        st.warning("Search completed, but no unique matching business listings were returned for this query.")
                    else:
                        # Convert JSON payload instantly into a beautiful visual spreadsheet
                        df = pd.DataFrame(leads_list)
                        
                        # Clean column headers for non-technical users
                        df.columns = ["Business Name", "Website URL", "Description Snippet", "Core Domain"]
                        
                        st.success(f"Success! Found {len(df)} fresh B2B leads for '{keyword}' in '{location}'.")
                        
                        # Display the visual data table to the user
                        st.dataframe(df, use_container_width=True)
                        
                        # Generate a clean download link to export data straight to Excel/CSV
                        csv_data = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Lead List as Excel/CSV Spreadsheet",
                            data=csv_data,
                            file_name=f"leadpulse_{keyword}_{location}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                else:
                    st.error(f"Server Error (Status Code: {response.status_code}). Please try again later.")
            except Exception as e:
                st.error(f"Connection Timeout: Your query requires deeper multi-page pagination analysis. Error: {str(e)}")
