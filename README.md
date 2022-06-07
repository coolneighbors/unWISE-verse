#Full Pipeline: Queries ALLWISE AWS database, converts to gif, uploads to zooniverse
Dependencies: Python3, panoptics cli, os, sys, csv

Dependency installation: 

os, sys, and csv libraries should be installed by default with most Python installations


Install panoptescli using the command: 

##pip install panoptescli


Usage:


input RA and DEC for each target in the targets.csv file

In cmd/powershell

##python spout.py

manifest.csv will be generated in current director
all png's for targets will be saved to pngs/ folder

----------------

Uploading to Zooniverse:

After manifest generation and png saving, user will be queried about whether they would like to save to Zoonivers
Program will end if no. If yes: 

User will input Zooniverse project ID and subject set name. 
Zooniverse credentials will be verified, if this is the first time running the program, user will input Zooniverse username and password
Note: password will not be shown on screen, just type as normal

If credentials have been previously entered, current user will be shown as 
Username [USER]: 
Hit enter twice to skip username and password entry. Otherwise, enter new username and password


Option to create new subject set for the Zooniverse project. If yes, program will generate new subject set and output a set ID:
[ID] {[NAME]}

Enter set ID in input section as prompted.

Data will be published.  


If no, enter known set ID into input section as prompted.

Data will be published.

Program will end. 