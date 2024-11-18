co_scraper.py:
    Scrapes codeocean.com to create a CSV of capsules to use in the benchmark.

csv_to_json.py:
    Takes a Google Sheet CSV of Hal capsules (https://docs.google.com/spreadsheets/d/1mBzLbG9AXRDlj1lqF-zEEWJOBJxTwMh_rC8kaMxt5b8/edit?usp=sharing) and converts it intoa  dataset JSON file.

hal.py:
    Converts CORE-Bench output JSONs into format to use for HAL using weave_utils.py