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
import math
import argparse
import calendar as Calendar
from sys import argv
from datetime import date, datetime, timedelta
from rich.console import Console #type: ignore

console = Console()

"""Default Parameters"""
MAX_WAIT = 600
DRIVER = None
AIM_PROD = 'https://bedrock.psu.ds.pdx.edu/aim/'
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

def updateRate(credentials, emp, odin, rates, startDate, endDate):
    """
    Updates the SOPE rates of the employee by ending the old rate and
    creating a new entry for the new SOPE rate.
    Params:
        credentials <obj> : login credentials
        emp <obj> : employee name and ODIN ID
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
                # Select day
                dayFinder(xpath, day)
            else:
                label = monthLabel.text.split(' ')
                mLabel = list(Calendar.month_name).index(label[0])
                yLabel = int(label[1])
                # Select the correct year, month, and day values from calendar
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
            console.print(f'An error has occurred when attempting to set the date.', style='bold red')
            sys.exit(1)

    def endDateRates(base, overtime, oncall, sope, endDate):
        """
        Wrapper function which will end date all of the current tier's rates.
        Params:
            base <string> : Row number of base rate
            overtime <string> : Row number of overtime rate
            oncall <string> : Row number of oncall rate
            sope <string> : Row number of sope rate
            endDate <string> : Date used to set the end of the old rate
        Returns:
            None
        """
        try:
            endDateRate(f'//*[@id="mainForm:SHOP_PERSON_RATES_EDIT_content:shopPersonRatesList:{base}:seqLink"]', endDate)
            endDateRate(f'//*[@id="mainForm:SHOP_PERSON_RATES_EDIT_content:shopPersonRatesList:{overtime}:seqLink"]', endDate)
            endDateRate(f'//*[@id="mainForm:SHOP_PERSON_RATES_EDIT_content:shopPersonRatesList:{oncall}:seqLink"]', endDate)
            if rates.SOPE != '0.00':
                endDateRate(f'//*[@id="mainForm:SHOP_PERSON_RATES_EDIT_content:shopPersonRatesList:{sope}:seqLink"]', endDate)
        except:
            console.print('Failed to end date current rates.', style='bold red')

    def endDateRate(xpath, endDate):
        """
        End date the rate linked to the provided xpath
        Params:
            xpath <string> : XPath to the line item link
            endDate <string> : Date used to set the end of the old rate
        Returns:
            None
        """
        rateLink = driver.find_element(by='xpath', value=xpath)
        rateLink.click()
        time.sleep(1)
        endPath = 'mainForm:SHOP_PERSON_RATES_ITEM_EDIT_content:endDateValue'
        datePicker(END, endDate, endPath)

    def setNewRates(rates, startDate):
        """
        Wrapper function that sets all of the new rates.
        Params:
            rates <obj> : Object containing all calculated rates
            startDate <string> : Starting date of the new rates
        Returns:
            None
        """
        # Set new rates
        setNewRate('R', 'I', rates.base, startDate)
        setNewRate('OT', 'I', rates.overtime, startDate)
        setNewRate('OC', 'I', rates.onCall, startDate)
        if rates.SOPE != '0.00':
            setNewRate('R', 'SOPE', rates.SOPE, startDate)

    def setNewRate(time_type, labor_class, rate, startDate):
        """
        Sets the new labor rates by specifying the type and class.
        Params:
            time_type <string> : Type of time (Regular, Overtime, On Call)
            labor_class <string> : Labor classification (typically only I or SOPE)
            rates <obj> : Object containing all of the new calculated rates
            startDate <string> : Starting date of the new rates
        Returns:
            None
        """
        try:
            startPath = 'mainForm:SHOP_PERSON_RATES_ITEM_EDIT_content:startDateValue'
            addBtn = driver.find_element(by='id', value='mainForm:SHOP_PERSON_RATES_EDIT_content:shopPersonRatesList:addRowButton')
            addBtn.click()
            driver.implicitly_wait(MAX_WAIT)
            # Set Time Type
            timeType = driver.find_element(by='xpath', value='//*[@id="mainForm:SHOP_PERSON_RATES_ITEM_EDIT_content:timeTypeZoom:level1"]')
            timeType.send_keys(time_type)
            # Set Labor Class
            laborClass = driver.find_element(by='xpath', value='//*[@id="mainForm:SHOP_PERSON_RATES_ITEM_EDIT_content:laborClassZoom:level1"]')
            laborClass.send_keys(labor_class)
            # Set rate
            rateField = driver.find_element(by='xpath', value='//*[@id="mainForm:SHOP_PERSON_RATES_ITEM_EDIT_content:laborRateValue"]')
            rateField.send_keys(rate)
            datePicker(START, startDate, startPath)
        except:
            console.print(f'Failed to set new {timeType}/{laborClass} rate.', style='bold red')

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
        findEmp(emp, odin)
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
         
        # Discover which row is what type of rate
        base_row = ''
        overtime_row = ''
        oncall_row = ''
        sope_row = ''
        if len(tableRows) != 0:
            for tr in range(len(tableRows)):
                labor_class = f'//*[@id="mainForm:SHOP_PERSON_RATES_EDIT_content:shopPersonRatesList:{tr}:ae_l_man_d_labor_class"]'
                time_type = f'//*[@id="mainForm:SHOP_PERSON_RATES_EDIT_content:shopPersonRatesList:{tr}:ae_l_man_d_time_type"]'
                if mainForm.find_element(by='xpath', value=time_type).text == 'R' and mainForm.find_element(by='xpath', value=labor_class).text == 'I':
                    base_row = tr
                if mainForm.find_element(by='xpath', value=labor_class).text == 'SOPE':
                    sope_row = tr
                if mainForm.find_element(by='xpath', value=time_type).text == 'OT':
                    overtime_row = tr
                if mainForm.find_element(by='xpath', value=time_type).text == 'OC':
                    oncall_row = tr
                else:
                    pass
        # End date rates
        endDateRates(base_row, overtime_row, oncall_row, sope_row, endDate)
        time.sleep(2)
        setNewRates(rates, startDate)
        time.sleep(10)
        
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
        console.print(f'An error has occurred when attempting to update the SOPE rate for {odin}. Abortting...', style='bold red')
        sys.exit(1)

def calcTierRates(base_rate, sope_rate=0.00):
    """
    Parse the CSV file in order to get the ODIN, rates, and dates
    Params:
        base_rate <float> : base rate of tier level
        sope_rate <float> : SOPE rate if provided
    Returns:
        rateObj <obj> : object containing new rates based on tier
    """ 
    # Define rateObj that will contain the new rate values
    class rateObj:
        def __init__(self) -> None:
            self.base = ''
            self.overtime = ''
            self.onCall = ''
            self.SOPE = ''
        def __str__(self) -> str:
            return """
            Base Rate (R/I): %s
            Overtime (OT/I): %s
            On Call (OC/I): %s
            SOPE (R/SOPE): %s
            """ % (self.base, self.overtime, self.onCall, self.SOPE)

    # Calculate different rates based on base rate
    overtime = float(base_rate * 1.5)
    onCall = float(base_rate / 6)

    # Convert to string
    base_rate = format(base_rate, '.2f')
    overtime = format(overtime, '.2f')
    onCall = format(onCall, '.2f')
    sope_rate = format(sope_rate, '.2f')

    # Create return object and set values
    rates = rateObj()
    rates.base = base_rate
    rates.overtime = overtime
    rates.onCall = onCall
    rates.SOPE = sope_rate
    
    return rates

def main(argv):
    # Set up command line parser with requirements
    parser = argparse.ArgumentParser(description='Updates the employee\'s rates based on the new tier\'s base rate. \
        Optional ability to update SOPE rate as well.')
    parser.add_argument('-n', '--name', help='Employee\'s lastName, firstName enclosed in quotation marks, comma separated.', required=True)
    parser.add_argument('-o', '--ODIN', help='Employee\'s ODIN', required=True)
    parser.add_argument('-d', '--startDate', help='Starting date of new tier rates', required=True)
    parser.add_argument('-t', '--tier', help='Base rate of tier', required=True)
    parser.add_argument('-s', '--sope', help='(Optional) New SOPE rate', required=False, default='0.00')
    args = parser.parse_args()

    # Reformat date argument if it isn't in right format
    startDate = args.startDate
    if '/' in startDate:
        startDate = startDate.replace('/', '-')
    startDate = datetime.strptime(startDate, '%m-%d-%Y')
    endDate = startDate + timedelta(days=-1)
    startDate = startDate.strftime("%B %d %Y")
    endDate = endDate.strftime("%B %d %Y")

    # Calculate rates based on the provided tier's base rate
    rates = calcTierRates(float(args.tier), float(args.sope))
    # Get login information
    credentials = decodePassword(os.path.join(UTILS_FOLDER, 'login.txt'))

    updateRate(credentials, args.name, args.ODIN.upper(), rates, startDate, endDate)

def cli():
    main(argv)

if __name__ == "__main__":
    main(argv)