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

google_drive_link = "https://drive.google.com/uc?export=download&id=1oo4aY58zMnbKKJDZX5YKK_e17zWpiw62"


# Load data
@st.cache_data
def load_data():
    # Try to load full dataset first, then fallback to Google Drive for online deployment
    full_filename = "snwk_competition_results_20251008_050303.json"
    full_filepath = os.path.join(ProjectPaths.DATA, full_filename)
    
    # Check if local file exists
    if os.path.exists(full_filepath):
        dataset_type = "Full Dataset (Local)"
        with open(full_filepath, "r", encoding="utf-8") as f:
            competitions_data = json.load(f)
    else:
        # Download from Google Drive
        try:
            st.info(" Laddar ner fullständig dataset från Google Drive...")
            response = requests.get(google_drive_link, timeout=60)
            response.raise_for_status()
            competitions_data = response.json()
            dataset_type = "Full Dataset (Google Drive)"
            st.success(" Dataset framgångsrikt nedladdat från Google Drive!")
        except Exception as e:
            st.error(f" Kunde inte ladda data från Google Drive: {str(e)}")
            st.error("Ingen data tillgänglig! Kontrollera att datafiler finns tillgängliga.")
            st.stop()
    
    # Display which dataset is being used
    st.sidebar.info(f"Using: {dataset_type}")

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
df_participants, dataset_type = load_data()

# Simple Streamlit test with your competition data
st.title("🐕 Statistik För NoseWork Sök 🐕")
st.write("En sammanställning av statistik från alla nosework sök registrerade hos SWNK. " \
        "Datan består av sök inom TSM/TEM -  NW1, NW2, NW3")

# Add data info
if "Google Drive" in dataset_type:
    st.info("🌐 **Info**: Full dataset loaded from Google Drive for online deployment.")

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

# Apply filters
filtered_df = df_participants.copy()
if selected_comp_type != 'All':
    filtered_df = filtered_df[filtered_df['typ'] == selected_comp_type]

filtered_df = filtered_df[filtered_df['typ_av_sök'] == selected_search_type]

if selected_class != 'All':
    filtered_df = filtered_df[filtered_df['klass'] == selected_class]


# Charts
st.header(f"📈 Statistik Enligt Filter ({len(filtered_df)} sök)")

# Points distribution
fig_points = px.histogram(
    filtered_df, 
    x = 'poäng', 
    title ='Poängdistribution',
    nbins = 10
)
st.plotly_chart(fig_points, use_container_width=True)

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
            labels={'mean': 'Average Points', 'stamtavlenamn': 'Dog Name'}
        )
        st.plotly_chart(fig_top_dogs, use_container_width=True)
    else:
        st.info("📊 Ingen data för topp-hundar: Inga hundar har minst 10 tävlingar med nuvarande filter.")



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
