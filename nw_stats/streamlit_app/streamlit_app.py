import streamlit as st
import pandas as pd
import plotly.express as px
import json
import sys
import requests
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from nw_stats.config import ProjectPaths
import os

dataset_link = "https://github.com/LokeNilsson/NWdata/releases/download/v1.0.0/snwk_competition_results_20251008_050303.json"


# Load data
@st.cache_data(show_spinner=False)
def load_data():
    # Try to load full dataset first, then fallback to sample for online deployment
    full_filename = "snwk_competition_results_20251008_050303.json"
    sample_filename = "sample_competition_results.json"
    
    full_filepath = os.path.join(ProjectPaths.DATA, full_filename)
    sample_filepath = os.path.join(ProjectPaths.DATA, sample_filename)
    
    # Check if local file exists (for local development)
    if os.path.exists(full_filepath):
        dataset_type = "Full Dataset (Local)"
        with open(full_filepath, "r", encoding="utf-8") as f:
            competitions_data = json.load(f)
    # elif os.path.exists(sample_filepath):
    #     dataset_type = "Sample Dataset (50 competitions)"
    #     with open(sample_filepath, "r", encoding="utf-8") as f:
    #         competitions_data = json.load(f)
    else:
        # Try to download from GitHub Releases
        try:
            # Create a placeholder for temporary messages
            status_placeholder = st.empty()
            status_placeholder.info(" Laddar ner fullständig dataset från GitHub Releases...")
            
            response = requests.get(dataset_link, timeout=120)
            response.raise_for_status()
            competitions_data = response.json()
            dataset_type = "Full Dataset (GitHub Releases)"
            
            # Clear the loading message and show brief success
            status_placeholder.empty()
            
        except Exception as e:
            st.error(f" Kunde inte ladda data från GitHub Releases: {str(e)}")
            st.error("För lokal användning: se till att din dataset-fil finns i data-mappen.")
            st.error("För online-deployment: kontrollera GitHub Release med dataset-filen.")
            st.stop()
    

    # Transform to dataframe (copy the function from your notebook)
    def convert_time_to_seconds(time_str):
        if pd.isna(time_str) or time_str == '':
            return None
        try:
            time_str = str(time_str).replace(',', '.')
            if ':' in time_str:
                parts = time_str.split(':')
                if len(parts) == 2:
                    minutes = float(parts[0])
                    seconds = float(parts[1])
                    return minutes * 60 + seconds
                elif len(parts) == 3:
                    hours = float(parts[0])
                    minutes = float(parts[1]) 
                    seconds = float(parts[2])
                    return hours * 3600 + minutes * 60 + seconds
            else:
                return float(time_str)
        except:
            return None

    def create_participants_dataframe(competitions_data):
        participants_list = []

        for comp in competitions_data:
            comp_date = comp.get('datum', '')
            comp_location = comp.get('plats', '')
            comp_type = comp.get('typ', '')
            comp_class = comp.get('klass', '')
            comp_organizer = comp.get('arrangör', '')
            comp_coordinator = comp.get('anordnare', '')

            for result_set in comp.get('resultat', []):
                search_type = result_set.get('sök', '')
                judges = result_set.get('domare', [])
                judge_names = ', '.join(judges) if judges else ''

                for participant in result_set.get('tabell', []):
                    participant_row = {
                        'klass': comp_class,
                        'datum': comp_date,
                        'plats': comp_location,
                        'typ': comp_type,
                        'arrangör': comp_organizer,
                        'anordnare': comp_coordinator,
                        'typ_av_sök': search_type,
                        'domare': judge_names,
                        'förare': participant.get('handler', ''),
                        'hund_namn': participant.get('dog_call_name', ''),
                        'stamtavlenamn': participant.get('dog_full_name', ''),
                        'hundras': participant.get('dog_breed', ''),
                        'start_position': participant.get('start_number', ''),
                        'placering': participant.get('placement', ''),
                        'poäng': participant.get('points', ''),
                        'fel': participant.get('faults', ''),
                        'tid': convert_time_to_seconds(participant.get('time', ''))
                    }
                    participants_list.append(participant_row)

        return pd.DataFrame(participants_list)

    return create_participants_dataframe(competitions_data), dataset_type

# Load the data
with st.spinner(""):  # Empty spinner to override default
    df_participants, dataset_type = load_data()

# Simple Streamlit test with your competition data
st.title("🐕 Statistik För NoseWork Sök 🐕")
st.write("En sammanställning av statistik från alla nosework sök registrerade hos SWNK. ")

# Add data info
if "Sample" in dataset_type:
    st.info(" **Online Demo**: Using sample dataset (50 competitions). For complete data with all competitions, download and run locally.")
elif "GitHub Releases" in dataset_type:
    st.info(" **Full Dataset**: Complete dataset loaded from GitHub Releases!")

# Basic data overview
st.header(" Översikt av data ")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Totala Sök", len(df_participants))
with col2:
    st.metric("Olika Hundraser", df_participants['hundras'].nunique())
with col3:
    st.metric("Olika Förare", df_participants['förare'].nunique())
with col4:
    st.metric("Olika Arrangörer", df_participants['arrangör'].nunique())

# Filter sidebar
st.sidebar.header("Filter")
selected_comp_type = st.sidebar.selectbox(
    "Typ av Tävling:",
    ['All'] + list(df_participants['typ'].unique())
)

selected_search_type = st.sidebar.selectbox(
    "Typ av Sök:",
    list(df_participants['typ_av_sök'].unique())
)

selected_class = st.sidebar.selectbox(
    "Klass:",
    ['All'] + list(df_participants['klass'].unique())
)

selected_ref = st.sidebar.selectbox(
    "Domare:",
    ['All'] + list(df_participants['domare'].unique())
)

selected_race = st.sidebar.selectbox(
    "Hundras:",
    ['All'] + list(df_participants['hundras'].unique())
)

# Author info in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("""      
**Data hämtat från:** SNWK (Svenska Nosework Klubben)  
**Senast uppdaterad:**  2025-10-07
**Skapad av:** Loke Nilsson  
**Frågor eller feedback?**   
📧 Loke@snowcrash.nu
""")


# Apply filters
filtered_df = df_participants.copy()
if selected_comp_type != 'All':
    filtered_df = filtered_df[filtered_df['typ'] == selected_comp_type]

filtered_df = filtered_df[filtered_df['typ_av_sök'] == selected_search_type]

if selected_class != 'All':
    filtered_df = filtered_df[filtered_df['klass'] == selected_class]

if selected_ref != 'All':
    filtered_df = filtered_df[filtered_df['domare'] == selected_ref]

if selected_race != 'All':
    filtered_df = filtered_df[filtered_df['hundras'] == selected_race]


# Charts
st.header(f" Statistik Enligt Filter ({len(filtered_df)} sök)")

# Points distribution
fig_points = px.histogram(
    filtered_df, 
    x = 'poäng', 
    title ='Poängdistribution',
    nbins = 10,
    labels={'poäng': 'Poäng'}
)
fig_points.update_layout(yaxis_title="Antal Sök")
st.plotly_chart(fig_points, use_container_width=True)

# Errors Distribution
fig_errors = px.histogram(
    filtered_df, 
    x = 'fel', 
    title ='Feldistribution',
    nbins = 10,
    labels={'fel': 'Fel'}
)
fig_errors.update_layout(yaxis_title="Antal Sök")
st.plotly_chart(fig_errors, use_container_width=True)

# Time Distribution
time_data = filtered_df[filtered_df['tid'].notna()].copy()
time_data['tid_kategori'] = pd.cut(
    time_data['tid'], 
    bins=[0, 30, 60, 120, 300, float('inf')],
    labels=['<30s', '30-60s', '1-2min', '2-5min', '>5min']
)

fig_time = px.histogram(
    time_data,
    x='tid_kategori',
    title='Tidsdistribution',
    labels={'tid_kategori': 'Tid'}
)
fig_time.update_layout(yaxis_title="Antal Sök")
st.plotly_chart(fig_time, use_container_width=True)

# Time vs Points Relationship (using binned heatmap for performance)
time_points_data = filtered_df[(filtered_df['tid'].notna()) & (filtered_df['poäng'].notna())].copy()
if len(time_points_data) > 0:
    # Create time bins for better performance
    time_points_data['tid_binned'] = pd.cut(
        time_points_data['tid'], 
        bins=10, 
        precision=0
    ).astype(str)
    
    # Create average points by time bin
    time_summary = time_points_data.groupby('tid_binned')['poäng'].agg(['mean', 'count']).reset_index()
    time_summary = time_summary[time_summary['count'] >= 5]  # Only bins with enough data
    
    fig_time_points = px.bar(
        time_summary,
        x='tid_binned',
        y='mean',
        title='Genomsnittlig Poäng per Tidskategori',
        labels={'tid_binned': 'Tid (sekunder)', 'mean': 'Genomsnittlig Poäng'},
        hover_data={'count': True}
    )
    fig_time_points.update_xaxes(tickangle=45)
    st.plotly_chart(fig_time_points, use_container_width=True)

# Start Position vs Placement Analysis
placement_data = filtered_df[(filtered_df['start_position'].notna()) & 
                           (filtered_df['placering'].notna())].copy()
# Convert to numeric to ensure proper plotting
placement_data['start_position'] = pd.to_numeric(placement_data['start_position'], errors='coerce')
placement_data['placering'] = pd.to_numeric(placement_data['placering'], errors='coerce')
placement_data = placement_data.dropna(subset=['start_position', 'placering'])

# Start Position vs Placement Analysis (using binned averages for performance)
placement_data = filtered_df[(filtered_df['start_position'].notna()) & 
                           (filtered_df['placering'].notna())].copy()
# Convert to numeric to ensure proper plotting
placement_data['start_position'] = pd.to_numeric(placement_data['start_position'], errors='coerce')
placement_data['placering'] = pd.to_numeric(placement_data['placering'], errors='coerce')
placement_data = placement_data.dropna(subset=['start_position', 'placering'])

if len(placement_data) > 0:
    # Create start position bins for better performance
    max_start = placement_data['start_position'].max()
    bin_size = max(1, int(max_start / 10))  # Create ~10 bins
    placement_data['start_binned'] = (
        (placement_data['start_position'] - 1) // bin_size * bin_size + 1
    ).astype(int)
    
    # Calculate average placement by start position bin
    placement_summary = placement_data.groupby('start_binned').agg({
        'placering': ['mean', 'count'],
        'start_position': 'mean'
    }).round(1)
    
    # Flatten column names
    placement_summary.columns = ['avg_placement', 'count', 'avg_start_pos']
    placement_summary = placement_summary.reset_index()
    placement_summary = placement_summary[placement_summary['count'] >= 5]  # Only bins with enough data
    
    fig_position_placement = px.bar(
        placement_summary,
        x='start_binned',
        y='avg_placement',
        title='Genomsnittlig Slutplacering per Startposition',
        labels={'start_binned': 'Startposition (grupp)', 'avg_placement': 'Genomsnittlig Slutplacering'},
        hover_data={'count': True, 'avg_start_pos': True}
    )
    # Lower values are better, so we want bars pointing down to be good
    st.plotly_chart(fig_position_placement, use_container_width=True)




# Top performing dogs (by average points)
if len(filtered_df) > 0:
    top_dogs = filtered_df.groupby('stamtavlenamn')['poäng'].agg(['mean', 'count']).reset_index()
    top_dogs = top_dogs[top_dogs['count'] >= 10]  # At least 10 competitions
    top_dogs = top_dogs.sort_values('mean', ascending=False).head(10)
    
    if len(top_dogs) > 0:
        fig_top_dogs = px.bar(
            top_dogs, 
            x='stamtavlenamn', 
            y='mean',
            title='Top 10 Hundar per genomsnittlig poäng (min 10 competitions)',
            labels={'mean': 'Genomsnittlig Poäng', 'stamtavlenamn': 'Stamtavlenamn'}
        )
        st.plotly_chart(fig_top_dogs, use_container_width=True)
    else:
        st.info(" Ingen data för topp-hundar: Inga hundar har minst 10 tävlingar med nuvarande filter.")



# Sample specific dog analysis
st.header(" Statistik per Hund")
dog_name = st.selectbox("Välj hund genom stamtavlenamn", filtered_df['stamtavlenamn'].unique())

dog_df = df_participants.copy()
if selected_comp_type != 'All':
    dog_df = dog_df[dog_df['typ'] == selected_comp_type]
if selected_class != 'All':
    dog_df = dog_df[dog_df['klass'] == selected_class]

if dog_name:
    dog_data = dog_df[dog_df['stamtavlenamn'] == dog_name]

    st.write(f"**{dog_name}** har genomfört {len(dog_data)} sök")

    # Performance by search type
    performance_by_search = dog_data.groupby('typ_av_sök')['poäng'].mean().reset_index()

    fig_dog_performance = px.bar(
        performance_by_search,
        x='typ_av_sök',
        y='poäng',
        title=f'{dog_name} - Genomsnittlig poäng för olika sök'
    )
    st.plotly_chart(fig_dog_performance, use_container_width=True)

    # Recent competitions
    searches_to_show = 10
    st.write(f"Senaste {searches_to_show} Sök:")
    recent_comps = dog_data.sort_values('datum', ascending=False).head(searches_to_show)
    st.dataframe(recent_comps[['datum', 'plats', 'typ_av_sök', 'poäng', 'placering']], use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>NoseWork Statistik Portal</strong></p>
    <p>Skapad av <strong>Loke Nilsson</strong> | Data från <a href="https://www.snwktavling.se/" target="_blank">SNWK</a></p>
    <p> Analyserar svenska nosework tävlingsresultat |  <a href="https://github.com/LokeNilsson/NWdata" target="_blank">Öppen källkod på GitHub</a></p>
</div>
""", unsafe_allow_html=True)
