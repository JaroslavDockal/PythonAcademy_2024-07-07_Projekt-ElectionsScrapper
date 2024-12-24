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
        python scraper.py <URL> <output_file.csv>

    This script checks if the provided URL contains 'volby.cz'.
    If valid, it calls `download_data(url)` to scrape either:
      - A single "detail" page (one municipality or region), or
      - A "list" page containing multiple links to individual municipalities
        (in which case it will follow each link and scrape the details).

    Finally, the data is saved as a CSV file (UTF-8 with BOM) by `save_to_csv()`.
    """
    if len(sys.argv) != 3:
        print("Usage: python scraper.py <URL> <output_file.csv>")
        sys.exit(1)

    url = sys.argv[1]
    output_file = sys.argv[2]

    if "volby.cz" not in url:
        print("Error: Provide a valid volby.cz URL (with or without 'www').")
        sys.exit(1)

    data = download_data(url)
    save_to_csv(data, output_file, url)
    print(f"Data saved to {output_file}")


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
                        "Number", "Name", "Voters in the list",
                        "Issued envelopes", "Valid votes",
                        plus any party names with their vote counts.
    """
    try:
        r = requests.get(url)
        r.raise_for_status()
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
                    "Number": code,
                    "Name": location
                }
                row_dict.update(detail_data)
                data_list.append(row_dict)
        else:
            # "Detail" page scenario
            detail_data = scrape_detail(url)
            data_list.append(detail_data)

        return data_list
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def scrape_detail(detail_url):
    """
    Scrapes information from a "detail" page representing a single municipality or region.

    It expects:
      - A summary table (usually the first <table>) containing data such as:
          "Voters in the list", "Issued envelopes", "Valid votes"
        at specific <td> indices (3, 4, and 7) based on the 2017 election layout.
      - One or more subsequent tables (index >= 1) that list parties and their vote counts.
        Each party is found in row <td>[1] (party name) and <td>[2] (vote count).

    Returns:
        dict: A dictionary with keys like:
              {
                "Voters in the list": <str>,
                "Issued envelopes": <str>,
                "Valid votes": <str>,
                "<Party Name A>": <str>,  # e.g. "123"
                "<Party Name B>": <str>,
                ...
              }
              Some fields may be missing if they are not found in the HTML structure.
    """
    result = {}
    r = requests.get(detail_url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')

    tables = soup.find_all('table')
    if not tables:
        return result

    # Extract summary data from the first table
    try:
        summary_rows = tables[0].find_all("tr")
        if len(summary_rows) > 2:
            tds = summary_rows[2].find_all("td")
            voters = tds[3].get_text(strip=True).replace('\xa0','')
            envelopes = tds[4].get_text(strip=True).replace('\xa0','')
            valid = tds[7].get_text(strip=True).replace('\xa0','')
            result["Voters in the list"] = voters
            result["Issued envelopes"] = envelopes
            result["Valid votes"] = valid
    except (IndexError, AttributeError):
        # If the table or cells are not in the expected format
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
            if name:
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
         "Number", "Name", "Voters in the list", "Issued envelopes", "Valid votes"
      3. Sort all remaining keys alphabetically (usually party names).
      4. Write to the specified output CSV file.

    Args:
        data (list of dict): The data to be saved.
        output_file (str): The path/name of the CSV file to be created.
        src_url (str): The source URL, used only for logging.
    """
    keys = set()
    for item in data:
        keys.update(item.keys())

    priority = ["Number", "Name", "Voters in the list", "Issued envelopes", "Valid votes"]
    final_keys = []

    for pk in priority:
        if pk in keys:
            final_keys.append(pk)
            keys.remove(pk)

    remainder = sorted(keys)
    final_keys.extend(remainder)

    with open(output_file, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=final_keys, delimiter=';')
        writer.writeheader()
        writer.writerows(data)

    print("-" * 50)
    print(f"Data scraped from: {src_url}")
    print(f"Saved to: {output_file}")
    print("Program closed!")
    print("-" * 50)


if __name__ == "__main__":
    main()
