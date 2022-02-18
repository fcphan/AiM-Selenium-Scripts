# Selenium Browser
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
import sys
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
WORKING_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
UTILS_FOLDER = os.path.join(WORKING_DIRECTORY, 'utils/')
CSV_FOLDER = os.path.join(WORKING_DIRECTORY, 'csv/')

def initializeDriver():
    """
    Initialize Chrome webdriver
    Params:
        None
    Returns:
        driver <webdriver> : Chrome webdriver with specified options
    """
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
    chromedriver = os.path.join(UTILS_FOLDER, 'chromedriver')
    driver = webdriver.Chrome(executable_path=chromedriver, options=options)
    driver.set_page_load_timeout(MAX_WAIT)
    driver.set_script_timeout(MAX_WAIT)

    return driver

def decodePassword(passFile):
    """
    Decodes the base64 password so we can use it to login
    Params:
        passFile <string> : name of file containing username
                            and base64 encrypted password
    Returns:
        login <obj>: unencrypted password
    """
    class credentials:
        def __init__(self) -> None:
            self.usr = ''
            self.pwd = ''
        def __str__(self) -> str:
            return """Username: %s \nPassword: %s""" % (self.usr, self.pwd)
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

def updateRate(credentials, emp, endDate, startDate):
    """
    Updates the SOPE rates of the employee by ending the old rate and
    creating a new entry for the new SOPE rate.
    Params:
        credentials <obj> : login credentials
        emp <obj> : employee ODIN ID, current SOPE rate, new SOPE rate being set
        endDate <date> : end date for the old SOPE rate
        startDate <date> : starting date for the new SOPE rate
    Returns:
        None
    """
    def findEmp(empName, empODIN):
        """
        Finds the employee profile using the employee's ODIN to search.
        In the event that multiple profiles appear, use the employee's
        name and ODIN to select the correct profile.
        Params:
            empName <string> : Employee's first and last name
            empODIN <string> : Employee's ODIN ID
        Returns:
            None
        """
        try:
            hrLink = driver.find_element(by='id', value='mainForm:menuListMain:HR')
            hrLink.click()
            empSearch = driver.find_element(by='id', value='mainForm:menuListMain:search_EMPLOYEE_VIEW')
            empSearch.click()
            empTextbox = driver.find_element(by='id', value='mainForm:ae_h_emp_e_shop_person')
            empTextbox.send_keys(empODIN)
            empFind = driver.find_element(by='id', value='mainForm:buttonPanel:executeSearch')
            empFind.click()
            
            browseXPATH = '//*[@id="mainForm:browse"]/tbody'
            browseFlag = driver.find_elements(by='xpath', value=browseXPATH)
            if not browseFlag:
                return
            else:
                lname, fname = empName.split(', ')
                rows = browseFlag[0].find_elements(by='xpath', value=f'{browseXPATH}/tr')
                for r in range(len(rows)):
                    if (driver.find_element(by='xpath', value=f'//*[@id="mainForm:browse:{r}:ae_h_emp_e_lname"]').text.upper() == lname.upper()  and
                    driver.find_element(by='xpath', value=f'//*[@id="mainForm:browse:{r}:ae_h_emp_e_fname"]').text.upper() == fname.upper() and
                    driver.find_element(by='xpath', value=f'//*[@id="mainForm:browse:{r}:ae_h_emp_e_shop_person"]').text == empODIN):
                        driver.find_element(by='xpath', value=f'//*[@id="mainForm:browse:{r}:ae_h_emp_e_shop_person"]').click()
                        time.sleep(1)
                        return
        except:
            console.print(f"An error has occurred when searching for {empODIN}'s Employee Profile.")
            sys.exit(1)

    def datePicker(flag, setDate, path):
        """
        Selects the given date from the calendar picker accessible by the given input
        field.
        Params:
            flag <int> : identifier for start or end date
            setDate <string> : start/end date for the rate
            path <string> : id of input field
        Returns:
            None
        """
        
        def dayFinder(xpath, datePart):
            """
            Parses the calendar table cells in order to find the correct day.
            Params:
                xpath <string> : XPATH of the calendar table
                datePart <int> : day that the function is searching for
            Returns:
                None
            """
            try:
                for r in range(4,10):
                    for c in range(1,8):
                        # reset each time or errors occur, not sure why
                        day = WebDriverWait(driver, MAX_WAIT).until(EC.presence_of_element_located((By.XPATH, xpath)))
                        dateXPATH = f'{xpath}/tr[{r}]/td[{c}]'
                        selectedDay = day.find_element(by='xpath',value=dateXPATH)
                        if(int(selectedDay.text) == datePart and selectedDay.get_attribute('class') != 'dayothermonth'):
                            console.print('Selecting correct day...', style='blue')
                            day.find_element(by='xpath',value=dateXPATH).click()
                            
                            # Click the done button to finish date entry
                            doneBtn = driver.find_element(by='xpath',value='//*[@id="mainForm:buttonPanel:done"]')
                            doneBtn.click()
                            return
            except:
                console.print(f'An error has occurred when trying to set the day.')
                sys.exit(1)

        try:
            dateField = driver.find_element(by='id', value=path)
            dateField.click()
            driver.implicitly_wait(MAX_WAIT)
            xpath = ''
            # Separate date into parts
            month, day, year = setDate.split(' ')
            long_month = month
            month = list(Calendar.month_name).index(month)
            day = int(day)
            year = int(year)
            # Select input field to modify
            if flag == START:
                xpath = '//*[@id="mainForm:SHOP_PERSON_RATES_ITEM_EDIT_content:shopPersonRatesGrid"]/tbody/tr[6]/td[2]/div/table/tbody'
            else:
                xpath = '//*[@id="mainForm:SHOP_PERSON_RATES_ITEM_EDIT_content:shopPersonRatesGrid"]/tbody/tr[7]/td[2]/div/table/tbody'
            calendar = WebDriverWait(driver, MAX_WAIT).until(EC.presence_of_element_located((By.XPATH, xpath)))
            # Select date
            monthLabel = calendar.find_element(by='xpath', value=f'{xpath}/tr[1]/td')
            if monthLabel.text == f'{long_month} {year}':
                console.print('Month/Year matches, selecting day...', style='bold green')
                # Select day
                dayFinder(xpath, day)

            else:
                console.print('Month/Year does not match, selecting correct date...', style='bold red')
                label = monthLabel.text.split(' ')
                mLabel = list(Calendar.month_name).index(label[0])
                yLabel = int(label[1])
                # Select the correct year, month, and day values from calendar
                console.print('Selecting correct year...', style='blue')
                while yLabel != year:
                    calendar = WebDriverWait(driver, MAX_WAIT).until(EC.presence_of_element_located((By.XPATH, xpath)))
                    driver.implicitly_wait(MAX_WAIT)
                    monthLabel = calendar.find_element(by='xpath', value=f'{xpath}/tr[1]/td')
                    label = monthLabel.text.split(' ')
                    yLabel = int(label[1])
                    if yLabel < year:
                        calendar.find_element(by='xpath',value=f'{xpath}/tr[2]/td[1]').click()
                    if yLabel > year:
                        calendar.find_element(by='xpath',value=f'{xpath}/tr[2]/td[5]').click()
                console.print('Selecting correct month...', style='blue')
                while mLabel != month:
                    calendar = WebDriverWait(driver, MAX_WAIT).until(EC.presence_of_element_located((By.XPATH, xpath)))
                    driver.implicitly_wait(MAX_WAIT)
                    monthLabel = calendar.find_element(by='xpath', value=f'{xpath}/tr[1]/td')
                    label = monthLabel.text.split(' ')
                    mLabel = list(Calendar.month_name).index(label[0])
                    if mLabel < month:
                        calendar.find_element(by='xpath',value=f'{xpath}/tr[2]/td[4]').click()
                    if mLabel > month:
                        calendar.find_element(by='xpath',value=f'{xpath}/tr[2]/td[2]').click()
                dayFinder(xpath, day)
        except:
            console.print(f'An error has occurred when attempting to set the date.')
            sys.exit(1)

    try:
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
        # Search for Employee Profile
        findEmp(emp.employee, emp.ODIN)
        # Enter Edit Mode
        editBtn = driver.find_element(by='id', value='mainForm:buttonPanel:edit')
        editBtn.click()
        # Open Labor Rates
        laborRates = driver.find_element(by='id', value='mainForm:sideButtonPanel:moreMenu_3')
        laborRates.click()
        # Wait for rates table to load
        driver.implicitly_wait(10)
        mainForm = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "mainForm:content")))
        tableRows = mainForm.find_elements(by='xpath', value='//*[@id="mainForm:SHOP_PERSON_RATES_EDIT_content:shopPersonRatesList"]/tbody/tr')
        row = ''
        # Find SOPE rate row in table
        for tr in range(len(tableRows)):
            if mainForm.find_element(by='xpath', value=f'//*[@id="mainForm:SHOP_PERSON_RATES_EDIT_content:shopPersonRatesList:{tr}:ae_l_man_d_labor_class"]').text == 'SOPE':
                row = tr
            else:
                pass
        # Open SOPE rate
        SOPElink = driver.find_element(by='xpath', value=f'//*[@id="mainForm:SHOP_PERSON_RATES_EDIT_content:shopPersonRatesList:{row}:seqLink"]')
        SOPElink.click()
        # End date old rate
        driver.implicitly_wait(MAX_WAIT)
        endPath = 'mainForm:SHOP_PERSON_RATES_ITEM_EDIT_content:endDateValue'
        startPath = 'mainForm:SHOP_PERSON_RATES_ITEM_EDIT_content:startDateValue'
        datePicker(END, endDate, endPath)
        console.print(f'End Dated previous SOPE rate with the date: {endDate}', style='bold green')
        time.sleep(2)
        # Create new SOPE rate line item
        addBtn = driver.find_element(by='xpath', value='//*[@id="mainForm:SHOP_PERSON_RATES_EDIT_content:shopPersonRatesList:addRowButton"]')
        addBtn.click()
        driver.implicitly_wait(MAX_WAIT)
        # Set Time Type
        timeType = driver.find_element(by='xpath', value='//*[@id="mainForm:SHOP_PERSON_RATES_ITEM_EDIT_content:timeTypeZoom:level1"]')
        timeType.send_keys('R')
        # Set Labor Class
        laborClass = driver.find_element(by='xpath', value='//*[@id="mainForm:SHOP_PERSON_RATES_ITEM_EDIT_content:laborClassZoom:level1"]')
        laborClass.send_keys('SOPE')
        # Set rate
        rateField = driver.find_element(by='xpath', value='//*[@id="mainForm:SHOP_PERSON_RATES_ITEM_EDIT_content:laborRateValue"]')
        rateField.send_keys(emp.newRate)
        datePicker(START, startDate, startPath)
        console.print(f'Start Dated new SOPE rate with the date: {startDate}', style='bold green')

        time.sleep(5)

        # Save and quit
        doneBtn = driver.find_element(by='xpath', value='//*[@id="mainForm:buttonPanel:done"]')
        doneBtn.click()

        # saveBtn = driver.find_element(by='xpath', value='//*[@id="mainForm:buttonPanel:save"]')
        # saveBtn.click()

        # For Testing purposes, click cancel
        cancelBtn = driver.find_element(by='xpath', value='//*[@id="mainForm:buttonPanel:cancel"]')
        cancelBtn.click()

        #close Chromedriver connection
        driver.quit()
    except:
        console.print(f'An error has occurred when attempting to update the SOPE rate for {emp.ODIN}. Abortting...')
        sys.exit(1)

def parseCSV(csvFile):
    """
    Parse the CSV file in order to get the ODIN, rates, and dates
    Params:
        csv <string> : name of csv file including extension
    Returns:
        SOPEarray <array> : array of objects contaning new SOPE data
    """ 
    # Define SOPEobj that will contain the data parsed from CSV
    class SOPEobj:
        def __init__(self) -> None:
            self.employee = ''
            self.ODIN = ''
            self.type = ''
            self.curRate = ''
            self.newRate = ''
            self.difference = ''
        def __str__(self) -> str:
            return """
            Employee: %s
            ODIN: %s
            Type: %s
            Current SOPE: %s
            Updated SOPE: %s
            Difference: %s
            """ % (self.employee, self.ODIN, self.type, self.curRate, self.newRate, self.difference)

    # Declare arrays for later use
    SOPEarray = []
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
        empIdx = fields.index('Employee')
        odinIdx = fields.index('ODIN')
        typeIdx = fields.index('Type')
        curIdx = fields.index('Current Rate')
        newIdx = fields.index('Updated Rate')
        difInx = fields.index('Difference')

        obj = None
        for row in rows:
            # If the row is populated, create a new obj to store data
            # Append object to array when finished with the row
            if row[empIdx] != '':
                obj = SOPEobj()
                obj.employee = row[empIdx]
                obj.ODIN = row[odinIdx]
                obj.type = row[typeIdx]
                obj.curRate = row[curIdx]
                obj.newRate = row[newIdx]
                obj.difference = row[difInx]
                SOPEarray.append(obj)
        return SOPEarray
    except:
        console.print('An error has occurred while reading the CSV file.', style='bold red')
        pass

def main(argv):
    if len(argv) != 2:
        console.print(f'Error: Incorrect number of arguments. Supplied {len(argv)-1}/1 arguments.', style='bold red')
        console.print('Run the following, replacing startDate with the start date for the new rates:', style='bold green')
        console.print("\tupdate-sope 'startDate'", style='blue')
    else:

        data = parseCSV(os.path.join(CSV_FOLDER, 'new_rates.csv'))
        credentials = decodePassword(os.path.join(UTILS_FOLDER, 'login.txt'))

        startDate = argv[1]
        if '/' in startDate:
            console.print('Reformatting date...', style='yellow')
            startDate = startDate.replace('/', '-')
        startDate = datetime.strptime(startDate, '%m-%d-%Y')
        endDate = startDate + timedelta(days=-1)
        startDate = startDate.strftime("%B %-d %Y")
        endDate = endDate.strftime("%B %-d %Y")

        for employee in data:
            updateRate(credentials, employee, endDate, startDate)
        
        """Test cases for individual profiles"""
        # updateRate(credentials, 'Huck, Sam', 'SHUCK', '14.37', '15.00', endDate, startDate) #common
        # updateRate(credentials, 'Phan, Francis', 'PHAN5', '14.37', '15.00', endDate, startDate) #unique

def cli():
    main(argv)

if __name__ == "__main__":
    main(argv)