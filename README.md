# Scraper for SUCUPIRA professors page

## Configuration file

The scraper can be configured with the `CONFIG.cfg` file

- `BROWSER`: The browser to use the webdriver with (`firefox` or `chrome`);
- `HEADLESS`: Whether to run with a headless webdriver or not (`true` or `false`);
- `IES_QUERY`: A query to search for the Instituição de Ensino Superior, from which the scraper will select the first result (e.g. `ufrj`, `universidade federal do rio de janeiro`, `31001017`).

## How to run

The scraper can be run from CLI (`script.py`) or from Jupyter (`notebook.ipynb`). After it finishes, the results will be saved into a CSV file with `;` separator and into an Excel file.