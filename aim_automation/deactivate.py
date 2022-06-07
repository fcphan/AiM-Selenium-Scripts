# Selenium Browser
from types import coroutine
from typing import Mapping
from selenium import webdriver #type: ignore
from selenium.webdriver.chrome import options #type: ignore
from selenium.webdriver.common import by #type: ignore
from selenium.webdriver.common.keys import Keys #type: ignore
from selenium.webdriver.common.action_chains import ActionChains #type: ignore
from selenium.webdriver.support.select import Select #type: ignore
# Selenium Wait
from selenium.webdriver.common.by import By #type: ignore
from selenium.webdriver.support.ui import WebDriverWait #type: ignore
from selenium.webdriver.support import expected_conditions as EC #type: ignore
# Utilities
import time
import string
import random
import os
import base64
import calendar as Calendar
from sys import argv
import argparse
from datetime import date, datetime, timedelta
from rich.console import Console #type: ignore

console = Console()

"""Default Parameters"""
MAX_WAIT = 600
DRIVER = None
AIM_PROD = 'https://bedrock.psu.ds.pdx.edu/'
AIM_TRAINING = 'https://bedrock.psu.ds.pdx.edu:8443/aimtraining/'
AIM_TEST = 'aimtest.fpm.pdx.edu' #kinda janky
URL = AIM_PROD
END = 0
START = 1
WORKING_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
UTILS_FOLDER = os.path.join(WORKING_DIRECTORY, 'utils/')

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
        login <obj>: unencrypted username and password
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

def deactivate_employee(credentials, empName, odin, endDate):
    """
    Deactivates the following:
    - User Security record
        - Clears role and requestor
    - Requestor Account
    - Employee Profile
        - Sets payroll status to inactive
        - End dates labor rates
        - Sets employee status to blank/null
    Params:
        odin <string> : odin of the user being deactivated
        endDate <string> : user's last day
    Returns:
        None
    """
    def deactivate_user_sec():
        """
        Deactivates User Security record. Clears the role, requestor, and changes status flag
        """
        def generate_password():
            """
            Generates a random alphanumeric password.
            """
            alphabets = list(string.ascii_letters)
            digits = list(string.digits)
            special_characters = list("!@#$%^&*()")
            pwd = []
            aCount = 5
            dCount = 6
            sCount = 4
            # Get random letters, numbers, and special characters and push to list
            for i in range(aCount):
                pwd.append(random.choice(alphabets))
            for i in range(dCount):
                pwd.append(random.choice(digits))
            for i in range(sCount):
                pwd.append(random.choice(special_characters))
            
            # shuffle resulting list a few times
            for i in range(5):
                random.shuffle(pwd)
            
            return "".join(pwd)

        sysAdmin = driver.find_element(by='id', value='mainForm:menuListMain:SYSADMN')
        sysAdmin.click()
        time.sleep(1)
        usrSec = driver.find_element(by='id', value='mainForm:menuList:search_USER_ADMIN_VIEW')
        usrSec.click()
        time.sleep(1)
        loginField = driver.find_element(by='id', value='mainForm:ae_s_sec_c_login')
        loginField.send_keys(odin)
        exeBtn = driver.find_element(by='id', value='mainForm:buttonPanel:executeSearch')
        exeBtn.click()
        time.sleep(1)
        record = driver.find_element(by='id', value='mainForm:browse:0:ae_s_sec_c_login')
        record.click()
        # Edit User Security
        editBtn = driver.find_element(by='id', value='mainForm:buttonPanel:edit')
        editBtn.click()
        time.sleep(2)
        # Set Password field with new, randomly generated password
        newPwd = generate_password()
        pwdField = driver.find_element(by='id', value='mainForm:USER_ADMIN_EDIT_content:password')
        pwdField.clear()
        pwdField.send_keys(newPwd)
        # Get list of assigned roles
        roleList = []
        driver.implicitly_wait(5)
        roleTable = driver.find_elements(by='xpath', value='//*[@id="mainForm:USER_ADMIN_EDIT_content:oldRoleList"]/tbody')
        if len(roleTable) != 0:
            roles = roleTable[0].find_elements(by='xpath', value='//*[@id="mainForm:USER_ADMIN_EDIT_content:oldRoleList"]/tbody/tr')
            if(len(roles) > 0):
                for r in range(len(roles)):
                    role = driver.find_element(by='xpath', value=f'//*[@id="mainForm:USER_ADMIN_EDIT_content:oldRoleList:{r}:ae_authz_principal_role_id_link"]')
                    roleList.append(role.text)
        # Open Roles list and untick assigned roles and tick NONE role
        print(roleList)
        time.sleep(1)
        driver.implicitly_wait(5)
        loadRoles = driver.find_element(by='xpath', value='//*[@id="mainForm:USER_ADMIN_EDIT_content:oldRoleList:link"]')
        loadRoles.click()
        time.sleep(1)
        allRoles = driver.find_elements(by='xpath', value='//*[@id="mainForm:ZOOM_ROLE_MULTI_SELECT_content:allRolesList"]/tbody/tr')
        for r in range(len(allRoles)):
            role = driver.find_element(by='id', value=f'mainForm:ZOOM_ROLE_MULTI_SELECT_content:allRolesList:{r}:ae_authz_role_id')
            if role.text in roleList or role.text == 'NONE':
                roleCheckbox = driver.find_element(by='id', value=f'mainForm:ZOOM_ROLE_MULTI_SELECT_content:allRolesList:{r}:check')
                roleCheckbox.send_keys(Keys.SPACE)
        doneBtn = driver.find_element(by='id', value='mainForm:buttonPanel:done')
        doneBtn.click()
        time.sleep(1)
        # Clear Requestor field
        defaultsLink = driver.find_element(by='id', value='mainForm:sideButtonPanel:moreMenu_0')
        defaultsLink.click()
        requestorField = driver.find_element(by='id', value='mainForm:USER_DEFAULTS_EDIT_content:CDOCZoom:level3')
        requestorField.clear()
        doneBtn = driver.find_element(by='id', value='mainForm:buttonPanel:done')
        doneBtn.click()
        time.sleep(1)
        # Deactivate User Security record
        activeFlag = driver.find_element(by='id', value='mainForm:USER_ADMIN_EDIT_content:activeValue')
        activeObj = Select(activeFlag)
        activeObj.select_by_value('N')
        time.sleep(1)

        # Cancel Button
        # cancelBtn = driver.find_element(by='id', value='mainForm:buttonPanel:cancel')
        # cancelBtn.click()

        # Save Button
        saveBtn = driver.find_element(by='id', value='mainForm:buttonPanel:save')
        saveBtn.click()

        # Return to WorkDesk
        home = driver.find_element(by='id', value='mainForm:headerInclude:backToDesktopAction1')
        home.click()

    def deactivate_requestor_account():
        #HR link
        hrLink = driver.find_element(by='id', value='mainForm:menuListMain:HR')
        hrLink.click()
        time.sleep(1)
        requestorSearch = driver.find_element(by='id', value='mainForm:menuListMain:search_REQUESTOR_QUICK_ENTRY_VIEW')
        requestorSearch.click()
        requestor = driver.find_element(by='id', value='mainForm:ae_s_usr_d_requestor')
        requestor.send_keys(odin)
        searchBtn = driver.find_element(by='id', value='mainForm:buttonPanel:executeSearch')
        searchBtn.click()
        time.sleep(1)
        driver.implicitly_wait(10)
        rqstr = driver.find_elements(by='id', value='mainForm:browse:0:ae_s_usr_d_requestor')
        if len(rqstr) != 0:
            rqstr[0].click()
            time.sleep(1)
            editBtn = driver.find_element(by='id', value='mainForm:buttonPanel:edit')
            editBtn.click()
            time.sleep(1)
            activeFlag = driver.find_element(by='id', value='mainForm:REQUESTOR_QUICK_ENTRY_EDIT_content:active')
            activeObj = Select(activeFlag)
            activeObj.select_by_value('N')
            time.sleep(1)

            # Cancel button
            # cancelBtn = driver.find_element(by='id', value='mainForm:buttonPanel:cancel')
            # cancelBtn.click()

            # Save button
            saveBtn = driver.find_element(by='id', value='mainForm:buttonPanel:save')
            saveBtn.click()
        driver.implicitly_wait(10)
        # Return to WorkDesk
        home = driver.find_element(by='id', value='mainForm:headerInclude:backToDesktopAction1')
        home.click()

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
            if(len(rows) == 1):
                driver.find_element(by='xpath', value=f'//*[@id="mainForm:browse:0:ae_h_emp_e_shop_person"]').click()
                time.sleep(1)
                return
            else:
                for r in range(len(rows)):
                    if (driver.find_element(by='xpath', value=f'//*[@id="mainForm:browse:{r}:ae_h_emp_e_lname"]').text.upper() == lname.upper()  and
                    driver.find_element(by='xpath', value=f'//*[@id="mainForm:browse:{r}:ae_h_emp_e_fname"]').text.upper() == fname.upper() and
                    driver.find_element(by='xpath', value=f'//*[@id="mainForm:browse:{r}:ae_h_emp_e_shop_person"]').text == empODIN):
                        driver.find_element(by='xpath', value=f'//*[@id="mainForm:browse:{r}:ae_h_emp_e_shop_person"]').click()
                        time.sleep(1)
                        return

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

    def deactivate_emp_profile():
        """
        Deactivates User Profile, end dates labor rates, sets payroll status to Inactive
        """
        findEmp(empName, odin)
        # Enter Edit Mode
        editBtn = driver.find_element(by='id', value='mainForm:buttonPanel:edit')
        editBtn.click()
        # Payroll Data
        payroll = driver.find_element(by='id', value='mainForm:sideButtonPanel:moreMenu_2')
        payroll.click()
        time.sleep(1)
        prStatus = driver.find_element(by='id', value='mainForm:EMPLOYEE_POSITION_DATA_EDIT_content:payrollStatusCodesZoom:level0')
        prStatus.clear()
        prStatus.send_keys('I')
        doneBtn = driver.find_element(by='id', value='mainForm:buttonPanel:done')
        doneBtn.click()
        time.sleep(1)
        # Open Labor Rates
        laborRates = driver.find_element(by='id', value='mainForm:sideButtonPanel:moreMenu_3')
        laborRates.click()
        time.sleep(1)
        # Wait for rates table to load
        driver.implicitly_wait(5)
        mainForm = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "mainForm:content")))
        tableRows = mainForm.find_elements(by='xpath', value='//*[@id="mainForm:SHOP_PERSON_RATES_EDIT_content:shopPersonRatesList"]/tbody/tr')
        if len(tableRows) != 0:
            for r in range(len(tableRows)):
                rateXPath = f'//*[@id="mainForm:SHOP_PERSON_RATES_EDIT_content:shopPersonRatesList:{r}:seqLink"]'
                end_date_rate(rateXPath)
        driver.implicitly_wait(5)
        doneBtn = driver.find_element(by='xpath', value='//*[@id="mainForm:buttonPanel:done"]')
        doneBtn.click()

        # Change active flag to inactive
        statusFlag = driver.find_element(by='id', value='mainForm:EMPLOYEE_EDIT_content:activeValue')
        statusObj = Select(statusFlag)
        statusObj.select_by_value('N')

        # Change employee type
        empFlag = driver.find_element(by='id', value='mainForm:EMPLOYEE_EDIT_content:empTypeValue')
        empObj = Select(empFlag)
        empObj.select_by_index(0)
        time.sleep(3)

        # Save changes
        saveBtn = driver.find_element(by='xpath', value='//*[@id="mainForm:buttonPanel:save"]')
        saveBtn.click()

        # If error modal pops up, hit yes
        errorModal = driver.find_elements(by='id', value='softErrorList')
        if len(errorModal) != 0:
            yesBtn = driver.find_element(by='id', value='mainForm:buttonControls:yes')
            yesBtn.click()

        # For Testing purposes, click cancel
        # cancelBtn = driver.find_element(by='xpath', value='//*[@id="mainForm:buttonPanel:cancel"]')
        # cancelBtn.click()

    def end_date_rate(xpath):
        """
        End date the rate linked to the provided xpath
        """
        rateLink = driver.find_element(by='xpath', value=xpath)
        rateLink.click()
        time.sleep(1)
        endPath = 'mainForm:SHOP_PERSON_RATES_ITEM_EDIT_content:endDateValue'
        datePicker(END, endDate, endPath)

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
    # User Security
    deactivate_user_sec()
    console.print(f'User Security record for {odin} has been deactivated.', style='green bold')
    # Requestor Account
    deactivate_requestor_account()
    console.print(f'Requestor Account for {odin} has been deactivated.', style='green bold')
    # Employee Profile
    deactivate_emp_profile()
    console.print(f'Employee Profile for {odin} has been deactivated.', style='green bold')
    time.sleep(2)
    driver.quit()

def main(argv):
    # Set up command line parser with requirements
    parser = argparse.ArgumentParser(description='Deactivates an employee completely. Includes User Security, Labor Rates, and Employee Profile.')
    parser.add_argument('-n', '--name', help='Employee\'s lastName, firstName enclosed in quotation marks, comma separated.', required=True)
    parser.add_argument('-o', '--ODIN', help='Employee\'s ODIN', required=True)
    parser.add_argument('-d', '--endDate', help='Employee\'s last working day', required=True)
    args = parser.parse_args()

    endDate = args.endDate
    if '/' in endDate:
        console.print('Reformatting date...', style='yellow')
        endDate = endDate.replace('/', '-')
    endDate = datetime.strptime(endDate, '%m-%d-%Y')
    endDate = endDate.strftime("%B %d %Y")

    credentials = decodePassword(os.path.join(UTILS_FOLDER, 'login.txt'))
    deactivate_employee(credentials, args.name, args.ODIN.upper(), endDate)

def cli():
    main(argv)

if __name__ == "__main__":
    main(argv)