# PanoptesPipeline
Pipeline for sending subjects to Zooniverse
Dependencies - Python3, panoptescli, matplotlib, csv

Instructions: 

in cmd/powershell

#For first use
#--------------------
panoptes configure

#input username and password
#password will not be shown on screen, just type as normal

#--------------------

python StarField_Manifest.py

# Input number of star fields you would like to generate
# Manifest will automatically be created


#create a new subject set
panoptes subject-set create [PROJECT ID] “SUBJECT SET NAME”

#output: subject set ID (string of numbers)

#upload data
panoptes subject-set upload-subjects [SUBJECT SET ID] manifest.csv 



