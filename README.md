# SNWK Competition Statistics

A comprehensive data collection and analysis toolkit for Swedish Nose Work Club (SNWK) competition results.

## Overview

This project provides tools to scrape, process, and analyze competition data from the Swedish Nose Work Club website. It includes automated data collection, data transformation utilities, and an interactive dashboard for exploring competition statistics.

## Features

- **Automated Data Collection**: Scrapes competition results from SNWK website
- **Incremental Updates**: Only collects new competitions, avoiding duplicates
- **Data Transformation**: Converts nested competition data to flat DataFrame format
- **Interactive Dashboard**: Streamlit-based web interface for data exploration
- **Statistical Analysis**: Tools for analyzing performance trends and statistics

## Project Structure

```
nw_stats/
├── data/                           # Competition data files (JSON)
├── notebooks/                      # Jupyter notebooks for analysis
│   └── testing_data.ipynb         # Data exploration and analysis
├── nw_stats/                      # Main package
│   ├── config.py                  # Project configuration
│   ├── data_collection/           # Data scraping modules
│   │   └── scrape_data.py        # Main scraping functionality
│   └── streamlit_app/             # Dashboard application
│       └── streamlit_app.py      # Interactive web dashboard
├── requirements.txt               # Python dependencies
├── setup.py                      # Package installation
└── README.md                     # This file
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone or download the project to your local machine

2. Navigate to the project directory:
   ```bash
   cd nw_stats
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

4. Install additional dependencies for the dashboard:
   ```bash
   pip install streamlit plotly
   ```

## Usage

### Data Collection

The data collection script automatically finds new competitions and scrapes their results:

```bash
python -m nw_stats.data_collection.scrape_data
```

**What it does:**
- Fetches competition lists from SNWK website (2020-2025)
- Identifies competitions not yet in your local data
- Extracts detailed results for new competitions
- Saves data to timestamped JSON files in the `data/` directory

**Output files:**
- `snwk_new_subpages_YYYYMMDD_HHMMSS.json` - Competition subpage metadata
- `snwk_competition_results_YYYYMMDD_HHMMSS.json` - Detailed results data

### Data Analysis

Use the Jupyter notebook for data exploration:

```bash
jupyter notebook notebooks/testing_data.ipynb
```

The notebook demonstrates:
- Loading competition data from JSON files
- Transforming nested data to flat DataFrame format
- Basic statistical analysis and data exploration
- Performance analysis by search type and competition class

### Interactive Dashboard

Launch the Streamlit dashboard for interactive data exploration:

```bash
streamlit run nw_stats/streamlit_app/streamlit_app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Data Structure

### Competition Data Format

Each competition record contains:

```json
{
  "url": "https://www.snwktavling.se/?page=showres&...",
  "datum": "2025-01-15",
  "plats": "Stockholm",
  "typ": "TEM",
  "klass": "NW2",
  "arrangör": "Svenska Nose Work Klubben",
  "anordnare": "Local Club Name",
  "resultat": [
    {
      "sök": "Behållare",
      "domare": ["Judge Name"],
      "tabell": [
        {
          "placement": 1,
          "dog_call_name": "Rex",
          "points": 100,
          "faults": 0,
          "time": "01:33,35",
          "start_number": 24,
          "handler": "Handler Name",
          "dog_full_name": "Full Registered Name",
          "dog_breed": "German Shepherd"
        }
      ]
    }
  ]
}
```


## Technical Details

### Data Collection Process

1. **Competition Discovery**: Fetches competition lists by year and type from SNWK
2. **Deduplication**: Compares URLs with existing data to find new competitions
3. **Subpage Extraction**: Identifies result subpages for each competition
4. **Results Parsing**: Extracts detailed participant data and results
5. **Data Storage**: Saves structured data to timestamped JSON files

### Web Scraping Approach

- Respectful scraping with configurable delays between requests
- Robust error handling for network issues and malformed data
- User-Agent headers and proper request formatting
- Parsing of JavaScript-generated button links for subpage discovery

## Dependencies

Core dependencies:
- `requests` - HTTP requests for web scraping
- `beautifulsoup4` - HTML parsing
- `pandas` - Data manipulation and analysis

Optional dependencies:
- `streamlit` - Interactive dashboard
- `plotly` - Interactive visualizations
- `jupyter` - Notebook interface for analysis

## Contributing

To contribute to this project:

1. Ensure proper error handling in data collection scripts
2. Follow existing code structure and documentation patterns
3. Test data transformation functions with sample data
4. Update this README if adding new features

## License

This project is licensed under the terms specified in the LICENSE file.

## Data Source

Competition data is collected from the Swedish Nose Work Club (SNWK) website at https://www.snwktavling.se/. Please respect their terms of service and use data responsibly.

## Support

For issues or questions:
1. Check that all dependencies are properly installed
2. Verify that the SNWK website structure hasn't changed
3. Ensure proper network connectivity for data collection
4. Review log messages for specific error information