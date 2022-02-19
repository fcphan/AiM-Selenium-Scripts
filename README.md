# Introduction

This project is built using Selenium in order to automate certain tasks in AiM that either need to be done multiple times for multiple items, or involves a lot of navigation between different modules. These tasks include, but are not limited to, the following: deactivating user accounts from AiM, batch updating SOPE rates in AiM for multiple profiles, and importing new assets and their related documentation.

# Getting Started

This project has a few pre-requisites that need to be fulfilled before working. The first is to install Python's Poetry. If Python has not already been installed, you can install it [here](https://www.python.org/ "Official Python website").

## Poetry

If you already have Python installed, you will need to install Poetry. The preferred method is to install it via `pipx`, though alternative methods can be found [here](https://python-poetry.org/docs/#installation "Official Poetry Documentation - Installation Methods"). If you do not have `pipx`, you can install it via `pip`, which comes with Python.

```
pipx install poetry
```

## Clone Repo

Afterwards, you will need to clone the repo if it hasn't been already. To do so, navigate to your working directory and enter the following:

```
git clone https://github.com/fcphan/AiM-Selenium-Scripts.git
```

## Chromium Driver

Next, you will need to download the Chromium driver that is compatible with your version of Google Chrome. The drivers can be found at https://chromedriver.chromium.org/downloads. After extracting the file, place it in the `aim_automation/utils` folder. Please note that the contents of this folder is included in the `.gitignore` file, and will not be tracked.

## Additional Files

At this point, you are mostly done setting up. The last required file is a file containing your login credentials to AiM. In the `aim_automation/utils` folder, create a file called `login.txt` and enter your credentials in the following format:

```
username
password
```

Please note that you should never enter in your password as plaintext. For this project, the password must be base64 encoded, which can be done [here](https://www.base64encode.org/ "Base64 Encoding and Decoding"). Please note that the contents of this folder is included in the `.gitignore` file, and will not be tracked.

From here on, any additional files will be dependant on your needs. Place any CSV files in `aim_automation/csv`, and any asset related documents in `aim_automation/asset_docs`. It is possible that the scripts will be modified later on to check subdirectories in `asset_docs`, but as of right now, extract all the documents and place them in this folder.

# [WIP] Commands

_There may be some edge cases that I either did not experience while testing or don't know about. Further modifications will have to be made to accommodate for them._

## Update SOPE Rates

End dates the existing SOPE rates and creates a new SOPE rate with the updated rate provided from the CSV file.

### Structure

```
update-sope-rates -csv -startDate
```

### Arguments

| Argument     | Description                                                                                                                              |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `-csv`       | name of csv file with new rates [see format here](#sope-rate-format). Enclose in double quotes (") if there are spaces in the file name. |
| `-startDate` | starting date of new SOPE rate in MM-DD-YYYY or MM/DD/YYYY format (ex. '11-20-2021')                                                     |

### Example

```
update-sope-rates new_rates.csv 11-20-2021
```

_Note: Replace `new_rates.csv` with the newest csv with SOPE rates before running._

## Deactivate Employee

Deactivates an employee's User Record, Requestor, Employee Profile, and end dates any Labor Rates.

### Structure

```
deactivate-employee -name -odin -endDate
```

### Arguments

| Argument   | Description                                                            |
| ---------- | ---------------------------------------------------------------------- |
| `-name`    | Employee's name in "Last, First" format (ex. 'Smith, John')            |
| `-odin`    | Employee's ODIN ID (ex. SMITH2)                                        |
| `-endDate` | last working day in MM-DD-YYYY or MM/DD/YYYY format (ex. '11-20-2021') |

### Example

`deactivate-employee 'Smith, John' SMITH2 '11-20-2021'`

## Import Assets

Imports a list of assets from a CSV file, as well as any documents (images) associated with the asset as long as it exists.

### Structure

```
import-assets -csv
```

### Arguments

| Arguments | Description                                                                                                                                                      |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `-csv`    | Name of the csv file containing asset information [see format here](#asset-importing-format). Enclose in double quotes (") if there are spaces in the file name. |

### Examples

```
import-assets new_assets.csv
import-assets "new assets.csv"
```

# CSV Formatting

Some commands use a specific CSV structure/format in order to parse the data from the file. Find and copy the correct formatting for the command you are attempting to run, replacing the example data with your own.

## SOPE Rate Format

The `update-sope-rates` command's specific formatting:

| Employee Name | ODIN  | Type       | Current Rate | Updated Rate | Start Date |
| ------------- | ----- | ---------- | ------------ | ------------ | ---------- |
| Smith, John   | SMITH | CLASSIFIED | $10.00       | $15.00       | 2-18-2022  |

## Asset Importing Format

The `import-assets` command's specific formatting:

| asset_tag | asset_type | asset_group | status_code | description                    | region      | facility    | property   | location | location_id | model | serial_number | extra_description | image_name |
| --------- | ---------- | ----------- | ----------- | ------------------------------ | ----------- | ----------- | ---------- | -------- | ----------- | ----- | ------------- | ----------------- | ---------- | ---------- |
| 123456    | SERIALIZED | AUTODOOR    | ACTIVE      | AUTODOOR INTERIOR BUTTON WIRED | REGION_NAME | MAIN CAMPUS | PROPERTY # | 929      |             |       |               |                   |            | 018080.jpg |
