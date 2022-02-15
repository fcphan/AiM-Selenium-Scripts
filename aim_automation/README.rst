[WIP] Commands
===
*There may be some edge cases that I either did not experience while testing or don't know about. Further modifcations will have to be made to accomodate for them.*


#
Update SOPE Rates
#
"
End dates the exisiting SOPE rates and creates a new SOPE rate with the updated rate provided from the CSV file.
"
Structure
---
    `update-sope-rates -startDate`
Arguments
---
| `-startDate`      starting date of new SOPE rate in MM-DD-YYYY or MM/DD/YYYY format (ex. '11-20-2021')

Example
---

    `update-sope-rates '11-20-2021'`

*Note: Replace `new_rates.csv` with the newest csv with SOPE rates before running.*

#
Deactivate Employee
#
"
Deactivates an employee's User Record, Requestor, Employee Profile, and end dates any Labor Rates.
"
Structure
---
    `deactivate-employee -name -odin -endDate`
Arguments
---
| `-name`         Employee's name in "Last, First" format (ex. 'Smith, John')
| `-odin`         Employee's ODIN ID (ex. SMITH2)
| `-endDate`      last working day in MM-DD-YYYY or MM/DD/YYYY format (ex. '11-20-2021')

Example
---
    `deactivate-employee 'Smith, John' SMITH2 '11-20-2021'`