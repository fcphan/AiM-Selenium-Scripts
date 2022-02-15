# Selenium Browser
from distutils.command.upload import upload
from pickle import FALSE, TRUE
import sys
from types import coroutine
from typing import Mapping
from selenium import webdriver #type: ignore
from selenium.webdriver.chrome import options #type: ignore
from selenium.webdriver.common import by #type: ignore
from selenium.webdriver.common.keys import Keys #type: ignore
from selenium.webdriver.common.action_chains import ActionChains #type: ignore
# Selenium Wait
from selenium.webdriver.common.by import By #type: ignore
from selenium.webdriver.support.ui import WebDriverWait #type: ignore
from selenium.webdriver.support import expected_conditions as EC #type: ignore
# Utilities
import time
import os
import base64
import csv
import calendar as Calendar
from sys import argv
from datetime import date, datetime, timedelta
from rich.console import Console #type: ignore

console = Console()

"""Default Parameters"""
MAX_WAIT = 600
DRIVER = None
AIM_PROD = 'go.pdx.edu/aim'
AIM_TRAINING = 'https://bedrock.psu.ds.pdx.edu:8443/aimtraining/'
AIM_TEST = 'aimtest.fpm.pdx.edu' #kinda janky
URL = AIM_TRAINING
START = 1
END = 0
DOCUMENT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'asset_docs/')

tags = []

def initializeDriver():
    """
    Initialize Chrome webdriver
    Params:
        None
    Returns:
        driver <webdriver> : Chrome webdriver with specified options
    """
    try:
        # Chrome Driver Options
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-extensions')
        options.add_argument('--kiosk-printing')
        options.add_argument('--test-type')
        options.add_argument('--disable-gpu')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # Create a new driver
        chromedriver = os.path.join(os.path.dirname(os.getcwd()), 'chromedriver') or os.path.join(os.path.dirname(os.getcwd()), 'chromedriver.exe')
        driver = webdriver.Chrome(executable_path=chromedriver, options=options)
        driver.set_page_load_timeout(MAX_WAIT)
        driver.set_script_timeout(MAX_WAIT)
        return driver
    except:
        console.print("Error: Failed to initialize webdriver.", style='bold red')
        sys.exit(1)

def decodePassword(passFile):
    """
    Decodes the base64 password so we can use it to login
    Params:
        passFile <string> : name of file containing username
                            and base64 encrypted password
    Returns:
        login <obj>: unencrypted username and password
    """
    class credentials:
        def __init__(self) -> None:
            self.usr = ''
            self.pwd = ''
        def __str__(self) -> str:
            return """Username: %s \nPassword: %s""" % (self.usr, self.pwd)
   
    try:
        # Open file and read in the encrypted password
        f = open(passFile, 'r')
        data = f.read().splitlines()
        f.close()
        username = data[0]
        encryption = data[1]
        # Decode the password and return the plaintext to caller
        encoded = encryption.encode('ascii')
        decoded = base64.b64decode(encoded)
        password = decoded.decode('ascii')
        login = credentials()
        login.usr = username
        login.pwd = password
        return login
    except:
        console.print('Error: Failed to load login credentials.', style='bold red')
        sys.exit(1)

def importAssets(credentials, asset):
    """
    Imports documents before creating a new asset profile. The documents will then be added to the asset as a related document.
    First document in image list will be set as asset photo.

    Params:
        Asset <object> : Object containing all information required to create a new asset
        Credentials <object> : Object containing login information
    Returns:
        Nothing is returned.
    """

    def importDocument(image):
        try:
            upload_str = DOCUMENT_FOLDER + image
            # Open System Administration
            sys_admin = driver.find_element(by='id', value='mainForm:menuListMain:SYSADMN')
            sys_admin.click()
            driver.implicitly_wait(MAX_WAIT)

            # Create new Document Profile
            doc_profile = driver.find_element(by='id', value='mainForm:menuListMain:new_DOCUMENT_PROFILE_VIEW')
            doc_profile.click()
            driver.implicitly_wait(MAX_WAIT)

            # Upload Image
            input = driver.find_element(by='xpath', value='//*[@id="mainForm:CHECKIN_DOCUMENT_content:newFileUploadWidget"]')
            input.send_keys(upload_str)
            
            # Click Done
            done_btn = driver.find_element(by='id', value='mainForm:buttonPanel:done')
            done_btn.click()
            driver.implicitly_wait(MAX_WAIT)

            # Set Document Type
            type_id = driver.find_element(by='id', value='mainForm:DOCUMENT_PROFILE_EDIT_content:type:typeId')
            type_id.send_keys('IMAGES')

            # Set Description
            desc = driver.find_element(by='id', value='mainForm:DOCUMENT_PROFILE_EDIT_content:ae_document_version_series_doc_name')
            desc.send_keys(image)

            # Save and grab Document ID
            save_btn = driver.find_element(by='id', value='mainForm:buttonPanel:save')
            save_btn.click()
            time.sleep(2)
            doc_uuid = driver.find_element(by='id', value='mainForm:DOCUMENT_PROFILE_VIEW_content:ae_document_version_series_doc_id')
            doc_id = doc_uuid.text

            # Return to dashboard and return document ID to main function
            home = driver.find_element(by='id', value='mainForm:headerInclude:backToDesktopAction1')
            home.click()
            driver.implicitly_wait(MAX_WAIT)

            return doc_id
        except:
            console.log('An error has occurred while uploading documents. Aborting...', style='bold red')
            sys.exit(1)

    def checkAsset(tag):
        # Open Asset Management Module
        asset_mgmt = driver.find_element(by='xpath', value='//*[@id="mainForm:menuListMain:ASSETMGT"]')
        asset_mgmt.click()
        driver.implicitly_wait(MAX_WAIT)

        # Search for Asset Tag
        search_btn = driver.find_element(by='id', value='mainForm:menuListMain:search_MASTER_ASSET_VIEW')
        search_btn.click()
        asset_field = driver.find_element(by='id', value='mainForm:ae_a_asset_e_asset_tag')
        asset_field.send_keys(tag)
        execute_btn = driver.find_element(by='id', value='mainForm:buttonPanel:executeSearch')
        execute_btn.click()

        # Check if anything exists
        driver.implicitly_wait(5)
        mainForm = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "mainForm:content")))
        results = mainForm.find_elements(by='xpath', value='//*[@id="mainForm:browse"]/tbody')
        if not results:
            result = FALSE
        else:
            result = TRUE

        # Return to dashboard and return document ID to main function
        home = driver.find_element(by='id', value='mainForm:headerInclude:backToDesktopAction1')
        home.click()
        driver.implicitly_wait(MAX_WAIT)

        # Return boolean based on search result
        return result

    try:
        # Image ID holder
        doc_id = []
        # Boolean to specify if asset tag already exists
        asset_exists = FALSE

        # Open AiM
        driver = initializeDriver()
        driver.get(URL)
        # Log into AiM instance
        username = driver.find_element(by='name', value='username')
        username.send_keys(credentials.usr)
        password = driver.find_element(by='name', value='password')
        password.send_keys(credentials.pwd)
        login = driver.find_element(by='id', value='login')
        login.click()
        driver.implicitly_wait(MAX_WAIT)

        # Import new document
        if asset.image != '':
            for img in asset.image:
                # Check if the document exists in the directory
                img_path = DOCUMENT_FOLDER + img
                img_exists = os.path.exists(img_path)
                # Upload document and add ID to list, otherwise pass
                if img_exists:
                    doc_id.append(importDocument(img))
                else:
                    pass

        # Check if there is a provided asset tag, and if it exists already
        if(asset.asset_tag != ''):
            asset_exists = checkAsset(asset.asset_tag)        

        # Open Asset Management Module
        asset_mgmt = driver.find_element(by='xpath', value='//*[@id="mainForm:menuListMain:ASSETMGT"]')
        asset_mgmt.click()
        driver.implicitly_wait(MAX_WAIT)

        # Create new Asset
        new_asset = driver.find_element(by='xpath', value='//*[@id="mainForm:menuListMain:new_MASTER_ASSET_VIEW"]')
        new_asset.click()
        driver.implicitly_wait(MAX_WAIT)

        # Enter Asset Tag -- Only use if specified to use
        if(asset.asset_tag != '' and asset_exists == FALSE):
            tag_field = driver.find_element(by='id', value='mainForm:MASTER_ASSET_EDIT_content:ae_a_asset_e_asset_tag')
            tag_field.clear()
            tag_field.send_keys(asset.asset_tag)

        # Enter description
        description_field = driver.find_element(by='id', value='mainForm:MASTER_ASSET_EDIT_content:ae_a_asset_e_description')
        description_field.send_keys(asset.description)

        # Enter Region
        region_field = driver.find_element(by='id', value='mainForm:MASTER_ASSET_EDIT_content:RFPLZoom3:RFPLZoom3-0')
        region_field.send_keys(asset.region)

        # Enter Facility
        facility_field = driver.find_element(by='id', value='mainForm:MASTER_ASSET_EDIT_content:RFPLZoom3:RFPLZoom3-1')
        facility_field.send_keys(asset.facility)

        # Enter Property
        property_field = driver.find_element(by='id', value='mainForm:MASTER_ASSET_EDIT_content:RFPLZoom3:RFPLZoom3-2')
        property_field.send_keys(asset.property)

        # Enter Location
        location_field = driver.find_element(by='id', value='mainForm:MASTER_ASSET_EDIT_content:RFPLZoom3:RFPLZoom3-3')
        location_field.send_keys(asset.location)

        # Enter Status
        status_field = driver.find_element(by='id', value='mainForm:MASTER_ASSET_EDIT_content:assetStatusZoom:level0')
        status_field.send_keys(asset.status)

        # Enter Asset Type
        type_field = driver.find_element(by='id', value='mainForm:MASTER_ASSET_EDIT_content:assetTypeGroupZoom:level0')
        type_field.send_keys(asset.asset_type)

        # Enter Asset Group
        group_field = driver.find_element(by='id', value='mainForm:MASTER_ASSET_EDIT_content:assetTypeGroupZoom:level1')
        group_field.send_keys(asset.asset_group)

        # Enter Manufacturer
        if asset.manufacturer != '':
            manufacturer_field = driver.find_element(by='id', value='mainForm:MASTER_ASSET_EDIT_content:manufactureZoom:level0')
            manufacturer_field.send_keys(asset.manufacturer)

        # Enter Model
        if asset.model != '':
            model_field = driver.find_element(by='id', value='mainForm:MASTER_ASSET_EDIT_content:model')
            model_field.send_keys(asset.model)

        # Enter Serial Number
        if asset.serial_no != '':
            serialno_field = driver.find_element(by='id', value='mainForm:MASTER_ASSET_EDIT_content:serialNo')
            serialno_field.send_keys(asset.serial_no)

        # Enter Extra Description
        if asset.extra_description != '':
            extra_desc_btn = driver.find_element(by='id', value='mainForm:sideButtonPanel:moreMenu_0')
            extra_desc_btn.click()
            driver.implicitly_wait(MAX_WAIT)
            extra_desc = driver.find_element(by='id', value='mainForm:ae_a_asset_e_long_desc')
            extra_desc.send_keys(asset.extra_description)
            done_btn = driver.find_element(by='id', value='mainForm:buttonPanel:done')
            done_btn.click()

        # Set Related Documents
        if doc_id:
            for doc in doc_id:
                related_btn = driver.find_element(by='id', value='mainForm:sideButtonPanel:moreMenu_20')
                related_btn.click()
                driver.implicitly_wait(MAX_WAIT)
                attach_btn = driver.find_element(by='id', value='mainForm:MASTER_ASSET_RELATED_DOCS_EDIT_content:docBrowse:addRelatedDocument')
                attach_btn.click()
                # Search for Document via ID
                guid_field = driver.find_element(by='id', value='mainForm:ae_document_version_series_doc_id')
                guid_field.send_keys(doc)
                execute_btn = driver.find_element(by='id', value='mainForm:buttonPanel:executeSearch')
                execute_btn.click()
                time.sleep(2)
                # Select Document from list
                first_res = driver.find_element(by='id', value='mainForm:browse:0:check')
                first_res.click()
                done_btn = driver.find_element(by='id', value='mainForm:buttonPanel:done')
                done_btn.click()
                time.sleep(2)
                done_btn = driver.find_element(by='id', value='mainForm:buttonPanel:done')
                done_btn.click()
                driver.implicitly_wait(MAX_WAIT)

                # Set Image
                image_btn = driver.find_element(by='id', value='mainForm:MASTER_ASSET_EDIT_content:repoAssetImage_add')
                image_btn.click()
                driver.implicitly_wait(MAX_WAIT)
                search_btn = driver.find_element(by='id', value='mainForm:buttonPanel:search')
                search_btn.click()
                driver.implicitly_wait(MAX_WAIT)
                # Search for Document via ID
                guid_field = driver.find_element(by='id', value='mainForm:ae_document_version_series_doc_id')
                guid_field.send_keys(doc_id[0])
                execute_btn = driver.find_element(by='id', value='mainForm:buttonPanel:executeSearch')
                execute_btn.click()
                time.sleep(2)
                # Select Document from list
                first_res = driver.find_element(by='id', value='mainForm:zoomTable:0:ae_document_version_series_doc_id')
                first_res.click()

        # Save and Quit
        save_btn = driver.find_element(by='id', value='mainForm:buttonPanel:save')
        save_btn.click()
        time.sleep(2)

        # Save tag so we know how far we got
        asset_tag = driver.find_element(by='id', value='mainForm:MASTER_ASSET_VIEW_content:ae_a_asset_e_asset_tag')
        tags.append(asset_tag.text)

        # Close driver
        driver.quit()
        return
    except:
        console.print('Failed to import new asset. Aborting...', style='red bold')
        sys.exit(1)

def parseCSV(csvFile):
    """
    Parse the CSV file in order to get the Asset information
    Params:
        csv <string> : name of csv file including extension
    Returns:
        AssetArray <array> : array of objects contaning new asset data
    """ 
    # Define AssetObj that will contain the data parsed from CSV
    class AssetObj:
        def __init__(self) -> None:
            self.asset_tag = ''
            self.description = ''
            self.status = ''
            self.asset_type = ''
            self.asset_group = ''
            self.region = ''
            self.facility = ''
            self.property = ''
            self.location = ''
            self.manufacturer = ''
            self.model = ''
            self.serial_no = ''
            self.extra_description = ''
            self.image = ''
        def __str__(self) -> str:
            return f"""
            Asset Tag: {self.asset_tag}
            Description: {self.description}
            Status: {self.status}
            Asset Type: {self.asset_type}
            Asset Group: {self.asset_group}
            Region: {self.region}
            Facility: {self.facility}
            Property: {self.property}
            Location: {self.location}
            Manufacturer: {self.manufacturer}
            Model: {self.model}
            Serial No: {self.serial_no}
            Extra Description: {self.extra_description}
            Image: {self.image}
            """ 

    # Declare arrays for later use
    AssetArray = []
    fields = []
    rows = []

    try:
        # Parse CSV
        with open(csvFile, 'r') as csvfile:
            csvreader = csv.reader(csvfile)
            fields = next(csvreader)
            for row in csvreader:
                rows.append(row)
        # Set Index so we know what column to find information
        assetTagIdx = fields.index('asset_tag')
        assetTypeIdx = fields.index('asset_type')
        assetGroupIdx = fields.index('asset_group')
        statusIdx = fields.index('status_code')
        descriptionIdx = fields.index('description')
        regionIdx = fields.index('region')
        facilityIdx = fields.index('facility')
        propertyIdx = fields.index('property')
        locationIdx = fields.index('location')
        manufacturerIdx = fields.index('manufacturer')
        modelIdx = fields.index('model')
        serialNoIdx = fields.index('serial_number')
        extraDescriptionIdx = fields.index('extra_description')
        imageIdx = fields.index('image_name')

        obj = None
        for row in rows:
            # If the row is populated, create a new obj to store data
            # Append object to array when finished with the row
            if row[assetTypeIdx] != '':
                obj = AssetObj()
                obj.asset_tag = row[assetTagIdx]
                obj.description = row[descriptionIdx]
                obj.status = row[statusIdx]
                obj.asset_type = row[assetTypeIdx]
                obj.asset_group = row[assetGroupIdx]
                obj.region = row[regionIdx]
                obj.facility = row[facilityIdx]
                obj.property = row[propertyIdx]
                obj.location = row[locationIdx]
                obj.manufacturer = row[manufacturerIdx]
                obj.model = row[modelIdx]
                obj.serial_no = row[serialNoIdx]
                obj.extra_description = row[extraDescriptionIdx]
                obj.image = row[imageIdx].split(', ')
                AssetArray.append(obj)
        return AssetArray
    except:
        console.print('An error has occurred while reading the CSV file.', style='bold red')
        pass

def main(argv):
    """
    Imports all assets from provided csv file. So long as the file is formatted correctly, the script will
    log into the AiM instance and upload the documents (if provided) and create the asset. Ensure that all images
    are located in asset_docs folder.
    
    Args:
        env <string> : AiM environment to test on
        csv <string> : CSV containing the assets being uploaded
    """
    # Parse Command Line arguments
    if len(argv) != 2:
        console.print(f'Error: Incorrect number of arguments. Supplied {len(argv)-1}/1 argument(s).', style='bold red')
        console.print("Run the following, replacing 'test.csv' with the csv name:", style='bold green')
        console.print("\timport-assets test.csv", style='blue')
    elif os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), argv[1])) == False:
        # Terminate if supplied file is not found in directory
        console.print(f"Error: The file '{argv[1]}' does not exists in the directory. Aborting...", style='bold red')
        sys.exit(1)
    elif os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'login.txt')) == False:
        # Terminates if login credentials file is not found in directory
        console.print("Error: Failed to find login information. Check to see if 'login.txt' exists.", style='bold red')
        sys.exit(1)
    else:
        console.print('Starting the import process...', style='bold purple')
        # Grab assets from CSV and login information
        assets = parseCSV(os.path.join(os.path.dirname(os.path.abspath(__file__)), argv[1]))
        credentials = decodePassword(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'login.txt'))

        # Single import
        # asset = assets[0]        
        # importAssets(credentials, asset)
            
        # Mass import
        for asset in assets:
            # print(asset)
            importAssets(credentials, asset)
            # Print asset tag and description for tracking purposes
            console.print(f'Added new asset: {tags[-1]} - {asset.description}')
        
        # Print list of assets successfully imported
        if tags:
            console.print('Finished adding new assets.', style='bold green')
            console.print(f'New assets are as follows: {", ".join(tags)}')

def cli():
    main(argv)

if __name__ == "__main__":
    main(argv)