Benchmark Utils Directory
=====================

This directory contains utility scripts used for data collection, processing, and fixing benchmark results.

Files:
------

1. co_scraper.py
   A web scraping script that collects computational capsule information from CodeOcean's website using Selenium.
   It extracts details such as field, date, title, description, author, programming language, and links for each
   capsule, saving the data to a CSV file (capsules.csv).

2. capsules.csv
   The output file from co_scraper.py containing the raw scraped data from CodeOcean. This CSV file serves as
   input for csv_to_json.py for further processing.

3. csv_to_json.py
   A data processing script that transforms the scraped capsules data from CSV to JSON format. It performs
   several important functions:
   - Filters capsules based on benchmark inclusion criteria
   - Validates and fixes JSON strings in result columns
   - Processes data into the required format for benchmarking
   - Can filter by specific splits (Train/Test/OOD) or capsule IDs
   - Outputs a properly formatted JSON file for use in benchmarking

4. fix_list_results.py
   A utility script that addresses a specific bug in the evaluation script where list values were not being
   properly handled. It:
   - Identifies result files containing list values
   - Re-evaluates results with fixed evaluation logic
   - Reports which results were affected (where correct list answers were previously marked wrong)
   - Updates result files with corrected evaluations
   This script is primarily documented for historical purposes as the results have since been fixed in the paper.
