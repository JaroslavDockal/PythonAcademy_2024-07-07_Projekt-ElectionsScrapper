# Czech Elections Scraper

This repository contains a Python script (`ElectionsScraper.py`) that downloads and extracts data from the [volby.cz](https://volby.cz) website (Czech parliamentary election results).

## Overview

- **Automatic detection** of either:
    - A "list" page containing multiple municipalities (and their links)
    - A "detail" page for a single municipality or region
- **Data scraped** includes:
    - `Registered` (number of registered voters)
    - `Envelopes` (issued envelopes)
    - `Valid` (valid votes)
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
   python ElectionsScraper.py <URL> <output_file.csv>
   ```

    - `<URL>`: must contain `"volby.cz"` (e.g., `https://volby.cz` or `https://www.volby.cz`).
    - `<output_file.csv>` is the name/path of the CSV file that will be created.

2. Behavior:
    - If `<URL>` leads to a page listing multiple municipalities (a "list" page), the script iterates each link to scrape individual details.
    - If `<URL>` is already a "detail" page for a single municipality, it just scrapes that page.

## Usage example

Elections results for the Olomouc district:

   1. Argument:  https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7102
   2. Argument: `Vysledky_Olomouc.csv`

Program execution:

```bash
python ElectionsScraper.py "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7102" Vysledky_Olomouc.csv
```

Program output:

```bash
Downloading data from the provided URL: https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7102
Data scraped from: https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7102
Saving to: Vysledky_Olomouc.csv
Data successfully saved to: Vysledky_Olomouc.csv
Program closed!
```

The generated CSV file contains columns such as:

- **Code** - Municipality code
- **Location** - Municipality name
- **Registered** - Number of registered voters
- **Envelopes** - Number of issued envelopes
- **Valid** - Number of valid votes
- Additional columns for each **political party** (in alphabetical order), listing the respective vote counts.

Example output in csv format:

```
Code;Location;Registered;Envelopes;Valid;...
552356;Babice;370;256;254;79;1;0;0;0;25;9;0;13;0;5;0;0;2;0;18;1;2;1;66;5;17;10;0;0
500526;Bělkovice-Lašťany;1801;1079;1069;333;1;0;1;1;81;75;1;97;6;6;1;0;8;2;44;7;15;18;153;32;104;83;0;0
500623;Bílá Lhota;931;568;565;164;0;0;0;1;73;62;5;31;0;6;0;2;3;0;20;0;6;4;81;12;53;42;0;0
...
```

## License

No explicit license is provided. You can consider applying a permissive license such as [MIT License](https://opensource.org/licenses/MIT).
