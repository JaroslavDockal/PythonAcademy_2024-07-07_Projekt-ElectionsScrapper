# Czech Elections Scraper

This repository contains a Python script (`ElectionsScraper.py`) that downloads and extracts data from the [volby.cz](https://volby.cz) website (Czech parliamentary election results).

## Overview

- **Automatic detection** of either:
    - A "list" page containing multiple municipalities (and their links)
    - A "detail" page for a single municipality or region
- **Data scraped** includes:
    - `Voters in the list`
    - `Issued envelopes`
    - `Valid votes`
    - Party names and their respective vote counts
- **Output** is a CSV file (UTF-8 with BOM, semicolon-delimited)

## Requirements

All necessary Python libraries are listed in **requirements.txt**. Install them with:

```bash
pip install -r requirements.txt
```

An example `requirements.txt` might look like:

```
requests==2.32.3
beautifulsoup4==4.12.3
```

## Usage

1. Run the scraper:

   ```bash
   python scraper.py <URL> <output_file.csv>
   ```

    - `<URL>`: A valid URL from `https://volby.cz` or `https://www.volby.cz`.
    - `<output_file.csv>`: Path/filename for the resulting CSV data.

2. Behavior:
    - If `<URL>` leads to a page listing multiple municipalities, the script iterates each link to scrape individual details.
    - If `<URL>` is already a detail (like one specific municipality), it just scrapes that page.

3. Example:

   ```bash
   python scraper.py "https://www.volby.cz/pls/ps2017nss/ps311?xjazyk=CZ&xkraj=14&xobec=598011&xvyber=8102" vysledek.csv
   ```

   This command scrapes the municipality "Baška" in the Moravskoslezský Kraj, storing the results in `vysledek.csv`.

## Output Format

The generated CSV file contains columns such as:

- **Number** (municipality code)
- **Name** (municipality name)
- **Voters in the list**
- **Issued envelopes**
- **Valid votes**
- One column per **party name**, each with its vote count

Example of a header row:

```
Number;Name;Voters in the list;Issued envelopes;Valid votes;Občanská demokratická strana;Česká pirátská strana;...
```

## License

No explicit license is provided. You can consider applying a permissive license such as [MIT License](https://opensource.org/licenses/MIT).
