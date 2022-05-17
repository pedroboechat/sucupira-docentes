"""
Scraper for SUCUPIRA professors page
"""

## Imports
# Standard
import os
import re
from time import sleep
from datetime import datetime as dt

# WebDriver
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager

# Selenium
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as ec

# Others
import pandas as pd
from bs4 import BeautifulSoup as bs
from dotenv import load_dotenv

## Configuration
# Change execution directory for file path
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Load configuration
load_dotenv("./CONFIG.cfg")
BROWSER = os.getenv("BROWSER").lower()
HEADLESS = os.getenv("HEADLESS").lower() == "true"
IES_QUERY = os.getenv("IES_QUERY").lower()

## WebDriver instance
if BROWSER == "firefox":
    # Add headless option
    options = webdriver.FirefoxOptions()
    options.headless = HEADLESS

    # Use service if the WebDriver is not in the PATH
    # service = webdriver.firefox.service.Service("<PATH/TO/DRIVER>")
    service = webdriver.firefox.service.Service(GeckoDriverManager().install())

    driver = webdriver.Firefox(
        service=service,
        options=options
    )

    action = ActionChains(driver)
elif BROWSER == "chrome":
    # Add headless option
    options = webdriver.ChromeOptions()
    options.headless = HEADLESS

    # Use service if the WebDriver is not in the PATH
    # service = webdriver.chrome.service.Service("<PATH/TO/DRIVER>")
    service = webdriver.chrome.service.Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(
        service=service,
        options=options
    )

    action = ActionChains(driver)
else:
    raise ValueError(f"Invalid browser: {BROWSER}")

## Gets SUCUPIRA
URL = "https://sucupira.capes.gov.br/sucupira/public/consultas/coleta/docente/listaDocente.xhtml"
driver.get(URL)

## Scrape page
### 1) Bypass cookie banner
# Click at cookie banner
driver.find_element(
    by = By.XPATH,
    value = '/html/body/div[5]/div/div/div[2]/button'
).click()

### 2) Set environment to UFRJ
# Get Instituição de Ensino Superior input field
ies_input = driver.find_element(
    by = By.XPATH,
    value = '//*[@id="form:j_idt30:inst:input"]'
)

# Send UFRJ IES code
ies_input.send_keys(IES_QUERY)

# Wait for options to be clickable
_ = WebDriverWait(driver, 10).until(
    ec.element_to_be_clickable((
        By.XPATH,
        '/html/body/form[2]/div/div[1]/div/div/div/fieldset/div[2]/div/div/div/div[2]/select'
    ))
)

# Waits 1 second
driver.implicitly_wait(1)
sleep(1)

# Get IES select element
ies_select = Select(driver.find_element(
    by = By.XPATH,
    value = '//*[@id="form:j_idt30:inst:listbox"]'
))

# Select first IES
ies_select.select_by_index(0)

### 3) Initialize important elements
# Wait for program selection to be clickable
try:
    _ = WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable((
            By.XPATH,
            '/html/body/form[2]/div/div[1]/div/div/div/fieldset/span[1]/div/div/div/div/select'
        ))
    )
except TimeoutException:
    _ = WebDriverWait(driver, 10).until(
        ec.visibility_of_element_located((
            By.XPATH,
            '/html/body/form[2]/div/div[1]/div/div/div/fieldset/span[1]/div/div/div/div/select'
        ))
    )

# Get program select element
program_select = Select(driver.find_element(
    by = By.XPATH,
    value = '/html/body/form[2]/div/div[1]/div/div/div/fieldset/span[1]/div/div/div/div/select'
))

### 4) Scrape elements
# Create empty results DataFrame
professors_df = pd.DataFrame()

# Number of programs for this IES
number_of_programs = len(program_select.options)
print("Number of programs:", number_of_programs - 1)
if number_of_programs < 2:
    raise ValueError("Error parsing programs")

# Get every program data
for index in range(1, len(program_select.options)):
    # Get program select element
    program_select = Select(driver.find_element(
        by = By.XPATH,
        value = '/html/body/form[2]/div/div[1]/div/div/div/fieldset/span[1]/div/div/div/div/select'
    ))

    # Get program search button
    search_button = driver.find_element(
        by = By.XPATH,
        value = '//*[@id="form:consultar"]'
    )

    # Select program by index
    program_select.select_by_index(index)

    # Get program raw information
    program_info = program_select.first_selected_option.text

    # Click search button
    driver.execute_script("arguments[0].click();", search_button)

    # Initialize page selector variable
    page_selector = None

    # Check whether there are results and get page selector element
    while True:
        try:
            page_selector = Select(WebDriverWait(driver, 3).until(
                ec.element_to_be_clickable((
                    By.XPATH,
                    '//select[@id="form:j_idt77:j_idt84"]'
                ))
            ))
            break
        except (NoSuchElementException, TimeoutException):
            print(index, "is empty...")
            break
        except StaleElementReferenceException:
            print(index, "is stale...")
    if page_selector is None:
        continue

    # For each page of the program results
    for page in range(len(page_selector.options)):
        print(page, end=" - ")

        # Select program results page 
        page_selector.select_by_index(page)

        # Waits 1 second if page changed
        if page > 0:
            driver.implicitly_wait(1)
            sleep(1)

        # Get table data
        while True:
            try:
                # Get table element after it has loaded and get outerHTML
                table_element = WebDriverWait(driver, 3).until(
                    ec.visibility_of_element_located((
                        By.XPATH,
                        '/html/body/form[2]/div/div[2]/div/div/div/span/span/span[2]/div/div/table'
                    ))
                ).get_attribute("outerHTML")

                # Parse outerHTML
                table = bs(
                    table_element,
                    'html.parser'
                )

                # Load HTML table to a DataFrame
                program_df = pd.read_html(str(table))[0]

                # Add raw program info
                program_df["programa"] = program_info

                # Concatenate new data to results DataFrame
                professors_df = pd.concat([
                    professors_df,
                    program_df
                ])
                print(index, f"was parsed! ({program_info}) -> {program_df.shape[0]}")
                break
            except (NoSuchElementException, TimeoutException):
                print(index, "is empty...")
                break
            except StaleElementReferenceException:
                print(index, "is stale...")
                break
        continue
    # Move page to the top
    action.move_to_element(search_button)

### 5) Closes WebDriver
# Close driver
driver.close()
print("Treating data")

## Data treatment
def extract_program(raw_program: str) -> list:
    """Extract program name and code from raw program info.

    Args:
        raw_program (str): Raw program information.

    Returns:
        list: A list of two elements: extracted name and code.
    """
    # Extract program code
    program_code = re.findall(
        r'\(\d{11}P\d\)',
        raw_program
    )[0][1:-1]

    # Extract program name
    program_name = re.sub(
        r'\s\s+',
        ' ',
        re.sub(
            r'\(\d{11}P\d\)',
            ' ',
            raw_program
        )
    ).strip().upper().replace(";","")

    return [
        program_name,
        program_code
    ]

# Drop row button column
professors_df = professors_df.drop("Unnamed: 2", axis = 1)

# Rename columns
professors_df = professors_df.rename(columns={
    "Docente": "docente",
    "Categoria": "categoria"
})

# Get extracted program data
extracted_program = professors_df["programa"].apply(extract_program)

# Add extracted data to DataFrame
professors_df["nome_do_programa"] = list(map(lambda x: x[0], extracted_program))
professors_df["codigo_do_programa"] = list(map(lambda x: x[1], extracted_program))

# Export data
print("Exporting data")
date = dt.strftime(dt.today(), "%d-%m-%Y_%Hh%M")
professors_df.to_excel(f"./docentes_sucupira_{date}.xlsx", index=False)
professors_df.to_csv(f"./docentes_sucupira_{date}.csv", sep=";", index=False)
print("Finished!")
