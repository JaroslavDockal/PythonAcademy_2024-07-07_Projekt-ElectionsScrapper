"""
Třetí projekt do Engeto Online Python Akademie

author: Jaroslav Dočkal

email: jaroslav.dockal@outlook.com

discord: jaroslav.dockal
"""

import requests
from bs4 import BeautifulSoup
import csv
import sys
from urllib.parse import urljoin

def main():
    """
    Entry point of the script.

    Usage:
        python ElectionsScraper.py <URL> <output_file.csv>

    This script checks if the provided URL contains 'volby.cz'.
    If valid, it calls `download_data(url)` to scrape either:
      - A single "detail" page (one municipality or region), or
      - A "list" page containing multiple links to individual municipalities
        (in which case it will follow each link and scrape the details).

    Finally, the data is saved as a CSV file (UTF-8 with BOM) by `save_to_csv()`.
    """
    try:
        if len(sys.argv) != 3:
            print("Error: Wrong number of arguments.")
            print("Usage: python ElectionsScraper.py <URL> <output_file.csv>")
            sys.exit(1)

        url = sys.argv[1]
        output_file = sys.argv[2]

        if "volby.cz" not in url:
            print("Error: Provide a valid volby.cz URL (with or without 'www').")
            sys.exit(1)

        print(f"Downloading data from the provided URL: {url}")

        data = download_data(url)
        save_to_csv(data, output_file, url)
        print(f"Data successfully saved to: {output_file}")
        print("Program closed!")
        print("-" * 50)

    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        sys.exit(0)

def download_data(url):
    """
    Determines whether the given URL represents a "list" page
    (containing multiple links to municipality details)
    or a single "detail" page (one municipality/region).

    - If it finds links to detail pages (in <td> elements),
      it iterates over those links, calls `scrape_detail()` for each,
      and accumulates the results in a list of dictionaries.
    - If it does not find such links, it assumes the URL is already a
      "detail" page and scrapes it directly via `scrape_detail()`.

    Returns:
        list of dict: Each dictionary represents one municipality/region.
                      Keys typically include:
                        "Code", "Location",
                        "Registered", "Envelopes", "Valid",
                        plus any party names with their vote counts.
    """
    try:
        r = requests.get(url)
        r.raise_for_status()

        if "Page not found!" in r.text:
            print("Error: The page indicates it was not found. The URL might be wrong.")
            sys.exit(1)

        soup = BeautifulSoup(r.text, 'html.parser')
        rows = soup.find_all('tr')
        data_list = []

        # Check if this page has municipality links in columns
        found_links = False
        for row in rows[2:]:
            cols = row.find_all('td')
            if cols and cols[0].find('a'):
                found_links = True
                break

        if found_links:
            # "List" page scenario
            for row in rows[2:]:
                cols = row.find_all('td')
                if not cols:
                    continue
                code = cols[0].get_text(strip=True)
                location = cols[1].get_text(strip=True)
                link = cols[0].find('a')
                if not link:
                    continue
                detail_url = unify_url_domain(url, link['href'])
                detail_data = scrape_detail(detail_url)
                row_dict = {
                    "Code": code,
                    "Location": location
                }
                row_dict.update(detail_data)
                data_list.append(row_dict)
        else:
            # "Detail" page scenario
            detail_data = scrape_detail(url)
            data_list.append(detail_data)

        return data_list

    except requests.exceptions.RequestException as e:
        print(f"Network-related error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while downloading or parsing the data: {e}")
        sys.exit(1)


def scrape_detail(detail_url):
    """
    Scrapes information from a "detail" page representing a single municipality or region.

    It expects:
      - A summary table (usually the first <table>) containing data such as:
          "Registered", "Envelopes", "Valid"
        at specific <td> indices (3, 4, and 7) based on the 2017 election layout.
      - One or more subsequent tables (index >= 1) that list parties and their vote counts.
        Each party is found in row <td>[1] (party name) and <td>[2] (vote count).

    Returns:
        dict: A dictionary with keys like:
              {
                "Registered": <str>,
                "Envelopes": <str>,
                "Valid": <str>,
                "<Party Name A>": <str>,  # e.g. "123"
                "<Party Name B>": <str>,
                ...
              }
              Some fields may be missing if they are not found in the HTML structure.
    """
    result = {}
    try:
        r = requests.get(detail_url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')

        tables = soup.find_all('table')
        if not tables:
            return result

        # Extract summary data from the first table
        summary_rows = tables[0].find_all("tr")
        if len(summary_rows) > 2:
            tds = summary_rows[2].find_all("td")
            voters = tds[3].get_text(strip=True).replace('\xa0','')
            envelopes = tds[4].get_text(strip=True).replace('\xa0','')
            valid = tds[7].get_text(strip=True).replace('\xa0','')
            result["Registered"] = voters
            result["Envelopes"] = envelopes
            result["Valid"] = valid

    except requests.exceptions.RequestException as e:
        print(f"Network-related error while scraping detail: {e}")
    except Exception as e:
        print(f"Error occurred while scraping the detail page: {e}")
    except (IndexError, AttributeError):
        print(f"Error: Unexpected table structure in URL: {detail_url}")
        pass

    # Extract party data from subsequent tables
    for pt in tables[1:]:
        rows = pt.find_all("tr")[2:]  # skip header rows
        for row in rows:
            tds = row.find_all("td")
            if len(tds) < 3:
                continue
            name = tds[1].get_text(strip=True)
            votes = tds[2].get_text(strip=True).replace('\xa0','')
            if name and name != "-":
                result[name] = votes

    return result


def unify_url_domain(base_url, relative_href):
    """
    Builds an absolute URL from the given base URL and a relative reference.

    This is necessary because the election site sometimes provides
    links like "ps2017nss/..." which are relative to the domain
    ("https://volby.cz" or "https://www.volby.cz").
    """
    return urljoin(base_url, relative_href)


def save_to_csv(data, output_file, src_url):
    """
    Saves a list of dictionaries (each representing a single municipality/region)
    to a CSV file. The CSV is encoded in UTF-8 with BOM and uses semicolons as delimiters.

    Steps:
      1. Collect all unique keys from the entire dataset.
      2. Prioritize the following keys in the header order:
         "Code", "Location", "Registered", "Envelopes", "Valid"
      3. Sort all remaining keys alphabetically (party names).
      4. Write to the specified output CSV file.

    Args:
        data (list of dict): The data to be saved.
        output_file (str): The path/name of the CSV file to be created.
        src_url (str): The source URL, used only for logging.
    """
    keys = set()
    for item in data:
        keys.update(item.keys())

    priority = ["Code", "Location", "Registered", "Envelopes", "Valid"]
    final_keys = []

    for pk in priority:
        if pk in keys:
            final_keys.append(pk)
            keys.remove(pk)

    remainder = sorted(keys)
    final_keys.extend(remainder)

    try:
        with open(output_file, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=final_keys, delimiter=';')
            writer.writeheader()
            writer.writerows(data)

        print(f"Data scraped from: {src_url}")
        print(f"Saving to: {output_file}")

    except PermissionError as e:
        print(f"Error: Cannot write to file '{output_file}' – permission denied or read-only file.")
        print(f"System message: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
