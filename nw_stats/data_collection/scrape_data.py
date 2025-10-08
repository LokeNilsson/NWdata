#!/usr/bin/env python3
"""
SNWK Competition Data Collection Script
======================================

This script streamlines the data collection process for SNWK competitions.
It automatically finds new competitions that haven't been collected yet and
runs the entire scraping process to add new data to existing collections.

Features:
- Finds competitions not yet collected
- Extracts subpages from new competitions  
- Scrapes detailed results data
- Merges with existing data without duplicates
- Robust error handling and logging

Author: Loke Nilsson
Date: 2025-10-07
"""

import json
import logging
import re
import requests
import time
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
import glob

from nw_stats.config import ProjectPaths


# Configuration
class Config:
    BASE_URL = "https://www.snwktavling.se/?page=resultat"
    YEARS_TO_SCRAPE = [2025, 2024, 2023, 2022, 2021, 2020]
    REQUEST_DELAY_SECONDS = 2.0
    SUBPAGE_DELAY_SECONDS = 0.5
    COMPETITION_TYPES = ["alla"]
    REQUEST_TIMEOUT = 30
    DATA_DIR = ProjectPaths.DATA
    
    REQUEST_HEADERS = {
        "User-Agent": "snwk-statistics-scraper loke@snowcrash.nu",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": BASE_URL,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8"
    }


# Setup logging
def setup_logging():
    """Configure logging for the application."""
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        force=True
    )
    return logging.getLogger(__name__)


logger = setup_logging()


def fetch_competitions_for_year(year: int, competition_type: str = "alla") -> List[Dict]:
    """
    Fetch competition links for a specific year and competition type.
    
    Args:
        year: The year to fetch competitions for
        competition_type: Type of competition to filter by
        
    Returns:
        List of competition dictionaries containing url, text, year, and type
    """
    logger.info(f"Fetching competitions for {year} (type: {competition_type})")
    
    post_data = {
        "tavTyp": competition_type,
        "klass": "alla",
        "year": str(year)
    }
    
    try:
        response = requests.post(
            Config.BASE_URL,
            data=post_data,
            headers=Config.REQUEST_HEADERS,
            timeout=Config.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        json_response = json.loads(response.text)
        
        if "body" not in json_response:
            logger.warning(f"No 'body' key in response for year {year}")
            return []
            
        html_content = json_response["body"]
        soup = BeautifulSoup(html_content, "html.parser")
        
        competitions = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            text = anchor.get_text(" ", strip=True)
            
            # Filter for competition-related links
            if any(keyword in href.lower() for keyword in ["page=showres", "page=", "tavling"]):
                # Convert relative URLs to absolute
                if href.startswith("?"):
                    full_url = f"https://www.snwktavling.se/{href}"
                else:
                    full_url = href
                    
                competitions.append({
                    "url": full_url,
                    "text": text,
                    "year": year,
                    "type": competition_type
                })
        
        logger.info(f"Found {len(competitions)} competitions for {year}")
        return competitions
        
    except requests.RequestException as e:
        logger.error(f"Network error fetching {year}: {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for {year}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching {year}: {e}")
        return []


def scrape_all_competitions() -> List[Dict]:
    """
    Main function to scrape competitions from all configured years and types.
    
    Returns:
        Complete list of all competitions found
    """
    all_competitions = []
    
    logger.info(f"Starting competition scrape for years: {Config.YEARS_TO_SCRAPE}")
    logger.info(f"Request delay: {Config.REQUEST_DELAY_SECONDS}s between requests")
    
    for i, year in enumerate(Config.YEARS_TO_SCRAPE):
        for competition_type in Config.COMPETITION_TYPES:
            competitions = fetch_competitions_for_year(year, competition_type)
            all_competitions.extend(competitions)
            
            # Add respectful delay between requests (except for the last one)
            if i < len(Config.YEARS_TO_SCRAPE) - 1:
                logger.info(f"Waiting {Config.REQUEST_DELAY_SECONDS}s before next request")
                time.sleep(Config.REQUEST_DELAY_SECONDS)
    
    return all_competitions


def extract_competition_subpages(competition_url: str, headers: Optional[Dict] = None) -> Dict:
    """
    Extract all sub-page URLs from a competition page.
    The links are in button onclick attributes, not regular <a> tags.
    """
    if headers is None:
        headers = Config.REQUEST_HEADERS
    
    try:
        response = requests.get(competition_url, headers=headers, timeout=Config.REQUEST_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        competition_data = {
            "main_url": competition_url,
            "subpages": []
        }
        
        # Look for buttons with onclick attributes that contain "Visa"
        buttons = soup.find_all("button", onclick=True)
        
        for button in buttons:
            button_text = button.get_text().strip()
            onclick_attr = button.get("onclick", "")
            
            # Check if this button is for sub-page navigation
            if "Visa" in button_text and "location=" in onclick_attr:
                # Extract URL from onclick="location='URL'"
                url_match = re.search(r"location='([^']+)'", onclick_attr)
                
                if url_match:
                    relative_url = url_match.group(1)
                    
                    # Convert to absolute URL
                    if relative_url.startswith("?"):
                        full_url = f"https://www.snwktavling.se/{relative_url}"
                    elif relative_url.startswith("/"):
                        full_url = f"https://www.snwktavling.se{relative_url}"
                    elif not relative_url.startswith("http"):
                        full_url = f"https://www.snwktavling.se/{relative_url}"
                    else:
                        full_url = relative_url
                    
                    subpage_info = {
                        "url": full_url,
                        "type": button_text,
                        "button_id": button.get("id", ""),
                        "onclick": onclick_attr
                    }
                    
                    competition_data["subpages"].append(subpage_info)
        
        return competition_data
        
    except Exception as e:
        logger.error(f"Error extracting subpages from {competition_url}: {e}")
        return {
            "main_url": competition_url,
            "subpages": [],
            "error": str(e)
        }


def parse_competition_results(comp_dict: Dict, headers: Optional[Dict] = None) -> Optional[Dict]:
    """
    Parse competition results from subpages with better text extraction.
    """
    if headers is None:
        headers = Config.REQUEST_HEADERS

    # ELITE competitions do not have subpages
    if not comp_dict['subpages']:
        return None
        
    competition_data = {
        "url": comp_dict["subpages"][0]['url'],
        "resultat": [],
    }

    # Save competition metadata with robust validation
    info_text = comp_dict.get("original_text", "")
    info_text_list = info_text.split()
    
    # Initialize with safe defaults
    competition_data.update({
        'datum': "",
        'plats': "",
        'typ': "",
        'klass': "",
        'arrangör': "",
        'anordnare': ""
    })
    
    if info_text_list:
        try:
            # Extract date (first element that looks like a date)
            for item in info_text_list:
                if re.match(r'\d{4}-\d{2}-\d{2}', item):
                    competition_data['datum'] = item
                    break
            else:
                # Fallback: use first element if it looks like a date format
                if info_text_list and re.match(r'\d{2,4}[-/]\d{1,2}[-/]\d{2,4}', info_text_list[0]):
                    competition_data['datum'] = info_text_list[0]
            
            # Extract location (second element, with validation)
            if len(info_text_list) > 1:
                # Skip invalid location values
                potential_location = info_text_list[1]
                if potential_location not in ['TEM', 'TSM', 'NW1', 'NW2', 'NW3', 'ELIT', 'Arrangör:', 'Anordnare:']:
                    competition_data['plats'] = potential_location
            
            # Extract competition type (look for TEM, TSM, etc.)
            for item in info_text_list:
                if item in ['TEM', 'TSM']:
                    competition_data['typ'] = item
                    break
            else:
                # Fallback: check position 3 but validate it's actually a competition type
                if len(info_text_list) > 3:
                    potential_typ = info_text_list[3]
                    # Only accept known competition types, reject invalid values like "-"
                    if potential_typ in ['TEM', 'TSM', 'Utomhus', 'Inomhus']:
                        competition_data['typ'] = potential_typ
            
            # Extract class (look for NW1, NW2, NW3, ELIT, etc.)
            for item in info_text_list:
                if re.match(r'^(NW[123]|ELIT)$', item):
                    competition_data['klass'] = item
                    break
            else:
                # Fallback: check position 5 but validate it's actually a class
                if len(info_text_list) > 5:
                    potential_klass = info_text_list[5]
                    # Only accept known class values, reject invalid values like "Arrangör" and "Inomhus"
                    if re.match(r'^(NW[123]|ELIT)$', potential_klass):
                        competition_data['klass'] = potential_klass
            
            # Extract organizer (between 'Arrangör:' and 'Anordnare:')
            try:
                start_arr = info_text_list.index('Arrangör:') + 1
                try:
                    end_arr = info_text_list.index('Anordnare:')
                    competition_data['arrangör'] = " ".join(info_text_list[start_arr:end_arr])
                except ValueError:
                    # No 'Anordnare:' found, take up to 5 words after 'Arrangör:'
                    competition_data['arrangör'] = " ".join(info_text_list[start_arr:start_arr+5])
            except ValueError:
                # No 'Arrangör:' found
                pass
            
            # Extract coordinator (everything after 'Anordnare:')
            try:
                start_anor = info_text_list.index('Anordnare:') + 1
                competition_data['anordnare'] = " ".join(info_text_list[start_anor:])
            except ValueError:
                # No 'Anordnare:' found
                pass
                
        except Exception as e:
            logger.warning(f"Failed to parse metadata for competition. Error: {e}")
            logger.warning(f"Text was: {info_text}")
            # Keep the safe defaults we set earlier

    # Go through moments of competition - TOT, M1, M2, M3, M4
    search_type = ""
    
    for page in comp_dict['subpages']:
        url = page['url']
        result_dict = {}
        
        try:
            response = requests.get(url, headers=headers, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            
            # Add respectful delay between sub-page requests
            time.sleep(Config.SUBPAGE_DELAY_SECONDS)
            
            # Add what type of search with validation
            if competition_data['typ'] == "TEM":
                if not search_type and page['type'].split()[-1] == "total":
                    result_dict['sök'] = "total"

                    h2_headers = soup.find_all("h2")
                    if h2_headers:
                        extracted_search_type = h2_headers[-1].text.split()[-1]
                        # Validate and clean the search type
                        if extracted_search_type and extracted_search_type not in ['', 'total']:
                            search_type = extracted_search_type
                    
                elif search_type and search_type.strip():  # Ensure search_type is not empty
                    result_dict['sök'] = search_type

            elif competition_data['typ'] == "TSM":
                h2_headers = soup.find_all("h2")
                raw_search_type = page['type'].split()[-1].removesuffix("sök")
                
                # Clean and standardize search type names
                if raw_search_type == "Behållar":
                    search_type = "Behållare"
                elif raw_search_type == "Fordons":
                    search_type = "Fordon"
                elif raw_search_type and raw_search_type.strip():  # Not empty
                    search_type = raw_search_type
                else:
                    search_type = ""

                # Only add if search_type is valid and not empty
                if search_type and search_type.strip():
                    result_dict['sök'] = search_type

            # Add referee information
            if page['type'].split()[-1] == "total":
                ref_div = soup.find("div", class_="domardiv")
                if ref_div:
                    text_list = ref_div.get_text().split()
                    if len(text_list) == 4:  # One ref
                        result_dict['domare'] = [f"{text_list[-2]} {text_list[-1]}"]
                    elif len(text_list) == 8:  # Two refs
                        result_dict['domare'] = [f"{text_list[2]} {text_list[3]}", f"{text_list[6]} {text_list[7]}"]
                    elif len(text_list) == 12:  # Three refs
                        result_dict['domare'] = [f"{text_list[2]} {text_list[3]}", f"{text_list[6]} {text_list[7]}", f"{text_list[-2]} {text_list[-1]}"]
                    else:
                        result_dict['domare'] = ["okänd"]
            else: 
                p = soup.find("p", string=re.compile("Domare"))
                if p:
                    match = re.search(r"Domare\s*[^:]*:\s*(.*)", p.get_text())
                    if match:
                        result_dict['domare'] = [match.group(1).strip()]
            
            # Add results for this branch
            branch_results = []
            results_list = soup.find("ul")
            if results_list:
                participants = results_list.find_all("li")
                
                # Get results for each participant
                for participant in participants:
                    participant_results = {}
                    # Get all text and work with it
                    participant_text = participant.get_text()

                    placement_match = re.search(r"Placering:\s*(\d+)", participant_text)
                    if placement_match:
                        participant_results["placement"] = int(placement_match.group(1))
                
                    # Look for pattern like "Name Surname & DogName"
                    strong_tags = participant.find_all("strong")
                    for strong in strong_tags:
                        strong_text = strong.get_text().strip()
                        if "&" in strong_text and "Placering" not in strong_text and "Totalpoäng" not in strong_text:
                            if " & " in strong_text:
                                handler, dog = strong_text.split(" & ", 1)
                                participant_results["dog_call_name"] = dog.strip()
                            break

                    # Extract total scores
                    total_points_match = re.search(r"Totalpoäng:\s*(\d+)", participant_text)
                    points_match = re.search(r"Poäng:\s*(\d+)", participant_text)
                    if total_points_match:
                        participant_results["points"] = int(total_points_match.group(1))
                    elif points_match:
                        participant_results["points"] = int(points_match.group(1)) 

                    # Faults count
                    total_faults_match = re.search(r"Totalfel:\s*(\d+)", participant_text)
                    faults_match = re.search(r"Fel:\s*(\d+)", participant_text)
                    if total_faults_match:
                        participant_results["faults"] = int(total_faults_match.group(1))
                    elif faults_match: 
                        participant_results["faults"] = int(faults_match.group(1))

                    # Total time 
                    total_time_match = re.search(r"Totaltid:\s*([\d:,]+)", participant_text)
                    time_match = re.search(r"Tid:\s*([\d:,]+)", participant_text)
                    if total_time_match:
                        participant_results["time"] = total_time_match.group(1).strip()
                    elif time_match:
                        participant_results["time"] = time_match.group(1).strip()

                    # Start number
                    start_match = re.search(r"Startnr:\s*(\d+)", participant_text)
                    if start_match:
                        participant_results["start_number"] = int(start_match.group(1))

                    # Handler name
                    handler_match = re.search(r"Förare:\s*([^\n\r]+)", participant_text)
                    if handler_match:
                        participant_results["handler"] = handler_match.group(1).strip()

                    # Dog name
                    dog_match = re.search(r"Hund:\s*([^\n\r]+)", participant_text)
                    if dog_match:
                        participant_results["dog_full_name"] = dog_match.group(1).strip()

                    # Dog breed
                    breed_match = re.search(r"Ras:\s*([^\n\r]+)", participant_text)
                    if breed_match:
                        participant_results["dog_breed"] = breed_match.group(1).strip()

                    branch_results.append(participant_results)

                result_dict['tabell'] = branch_results
                competition_data['resultat'].append(result_dict)

        except Exception as e:
            logger.error(f"Error parsing competition {url}: {e}")
            return None
        
    return competition_data


def get_existing_competition_urls() -> Set[str]:
    """
    Get all competition URLs that have already been processed.
    
    Returns:
        Set of URLs that have already been collected
    """
    existing_urls = set()
    
    # Check existing result files
    result_files = glob.glob(str(Config.DATA_DIR / "snwk_competition_results_*.json"))
    
    for result_file in result_files:
        try:
            with open(result_file, "r", encoding="utf-8") as f:
                results = json.load(f)
                for result in results:
                    if "url" in result:
                        existing_urls.add(result["url"])
        except Exception as e:
            logger.warning(f"Error reading existing results file {result_file}: {e}")
    
    logger.info(f"Found {len(existing_urls)} existing competition URLs")
    return existing_urls


def find_new_competitions(all_competitions: List[Dict], existing_urls: Set[str]) -> List[Dict]:
    """
    Find competitions that haven't been processed yet.
    
    Args:
        all_competitions: List of all available competitions
        existing_urls: Set of URLs that have already been processed
        
    Returns:
        List of new competitions to process
    """
    new_competitions = []
    
    for competition in all_competitions:
        # The URL in results data has additional parameters, so we need to match the base competition
        comp_url = competition["url"]
        
        # Check if this competition has already been processed by looking for the base URL pattern
        already_processed = False
        for existing_url in existing_urls:
            # Extract the competition identifier from both URLs for comparison
            if "arr=" in comp_url and "arr=" in existing_url:
                comp_id = comp_url.split("arr=")[1].split("&")[0]
                existing_id = existing_url.split("arr=")[1].split("&")[0]
                if comp_id == existing_id:
                    already_processed = True
                    break
        
        if not already_processed:
            new_competitions.append(competition)
    
    logger.info(f"Found {len(new_competitions)} new competitions to process")
    return new_competitions


def save_data_with_timestamp(data: List[Dict], filename_prefix: str) -> str:
    """
    Save data to a JSON file with timestamp.
    
    Args:
        data: Data to save
        filename_prefix: Prefix for the filename
        
    Returns:
        Path to the saved file
    """
    Config.DATA_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = Config.DATA_DIR / f"{filename_prefix}_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(data)} items to {filename}")
    return str(filename)


def main():
    """
    Main execution function that orchestrates the entire data collection process.
    """
    logger.info("Starting SNWK Competition Data Collection")
    logger.info("=" * 50)
    
    try:
        # Step 1: Get existing competition URLs
        logger.info("Step 1: Checking existing data...")
        existing_urls = get_existing_competition_urls()
        
        # Step 2: Fetch all current competitions
        logger.info("Step 2: Fetching current competitions...")
        all_competitions = scrape_all_competitions()
        logger.info(f"Found {len(all_competitions)} total competitions")
        
        # Step 3: Find new competitions
        logger.info("Step 3: Identifying new competitions...")
        new_competitions = find_new_competitions(all_competitions, existing_urls)
        
        if not new_competitions:
            logger.info("No new competitions found. Data collection is up to date.")
            return
        
        logger.info(f"Processing {len(new_competitions)} new competitions...")
        
        # Step 4: Extract subpages for new competitions
        logger.info("Step 4: Extracting subpages for new competitions...")
        new_subpages = []
        
        for i, competition in enumerate(new_competitions, 1):
            logger.info(f"Processing subpages {i}/{len(new_competitions)}: {competition.get('text', '')[:50]}...")
            
            subpage_data = extract_competition_subpages(competition["url"])
            
            # Add original competition metadata
            subpage_data.update({
                "original_text": competition.get("text", ""),
                "year": competition.get("year", ""),
                "type": competition.get("type", "")
            })
            
            new_subpages.append(subpage_data)
            
            # Add delay between requests
            if i < len(new_competitions):
                time.sleep(Config.REQUEST_DELAY_SECONDS)
        
        # Save subpages data
        subpages_file = save_data_with_timestamp(new_subpages, "snwk_new_subpages")
        
        # Step 5: Extract detailed results
        logger.info("Step 5: Extracting detailed results...")
        new_results = []
        
        for i, subpage_data in enumerate(new_subpages, 1):
            logger.info(f"Processing results {i}/{len(new_subpages)}: {subpage_data.get('original_text', '')[:50]}...")
            
            result = parse_competition_results(subpage_data)
            if result:
                new_results.append(result)
            
            # Add delay between competitions
            time.sleep(Config.REQUEST_DELAY_SECONDS)
        
        # Step 6: Save new results
        logger.info("Step 6: Saving new results...")
        results_file = save_data_with_timestamp(new_results, "snwk_competition_results")
        
        # Final summary
        logger.info("=" * 50)
        logger.info("Data collection completed successfully!")
        logger.info(f"New competitions processed: {len(new_competitions)}")
        logger.info(f"New results collected: {len(new_results)}")
        logger.info(f"Subpages saved to: {subpages_file}")
        logger.info(f"Results saved to: {results_file}")
        
        # Generate summary statistics
        total_subpages = sum(len(comp["subpages"]) for comp in new_subpages)
        logger.info(f"Total sub-pages processed: {total_subpages}")
        if new_subpages:
            logger.info(f"Average sub-pages per competition: {total_subpages/len(new_subpages):.1f}")
        
    except KeyboardInterrupt:
        logger.info("Data collection interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error during data collection: {e}")
        raise


if __name__ == "__main__":
    main()