import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
from tqdm import trange

capsules = []
fails = 0
for page_num in trange(1, 52):
    # Set up Selenium webdriver
    driver = webdriver.Chrome()  # Replace with the path to your Chrome webdriver

    # Navigate to the URL
    url = f"https://codeocean.com/explore?page={page_num}&filter=all"
    driver.get(url)

    # Wait for the elements to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'CardWrapper-sc-1xv7cv1-4'))
    )

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'Field-sc-fnpy6g-0'))
    )

    # Find elements by one of the class names using
    elements = driver.find_elements(By.CLASS_NAME, 'CardWrapper-sc-1xv7cv1-4')

    # Process the elements as needed
    for element in elements[(page_num-1)*100:(page_num)*100]:
        try:
            field = element.find_element(By.CLASS_NAME, 'Field-sc-fnpy6g-0')
            date = element.find_element(By.CLASS_NAME, 'PublishDate-sc-1xv7cv1-7')
            title = element.find_element(By.CLASS_NAME, 'CapsuleTitle-sc-jty72y-1')
            description = element.find_element(By.CLASS_NAME, 'CapsuleDescriptionWrapper-sc-1xv7cv1-11')
            author = element.find_element(By.CLASS_NAME, 'CapsuleAuthors-sc-1xv7cv1-2')
            language = element.find_element(By.CLASS_NAME, 'BadgesContainer-sc-1xv7cv1-3')
            language = language.find_element(By.CSS_SELECTOR, 'div[data-test="language-badge"]')
            language = language.get_attribute('class').split()[1]
            link = element.find_element(By.CLASS_NAME, 'OpenCapsule-sc-1pe5kk7-0')
            link = link.get_attribute('href')

            capsule = {
                "field": field.text,
                "date": date.text,
                "title": title.text,
                "description": description.text,
                "author": author.text,
                "language": language,
                "link": link,
            }
            capsules.append(capsule)
        except Exception as e:
            print(str(e))
            fails += 1
            continue
    # Close the webdriver
    driver.quit()

# Define the path to the output CSV file
csv_file = 'capsulses.csv'
# Write the capsules array to the CSV file
with open(csv_file, 'w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=capsules[0].keys())
    writer.writeheader()
    writer.writerows(capsules)
# Print a success message
print("Capsules array has been written to capsules.csv")
print(f"Scraped {len(capsules)} capsules")
print(f"Failed to scrape {fails} capsules")
csv_file = '/Users/zss/Projects/rab/code_ocean/capsules.csv'