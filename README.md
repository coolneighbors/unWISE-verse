[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6864030.svg)](https://doi.org/10.5281/zenodo.6864029)
# unWISE-verse
An integrated astronomical data collection and Zooniverse upload pipeline using the [Panoptes-Client](https://github.com/zooniverse/panoptes-python-client).

## Description
unWISE-verse allows a user to download data from a collection of WISE targets using the WiseView API, manipulate the images 
from the WiseView server, and upload the data to a Zooniverse subject set in the form of flipbooks. In addition, users 
have the option to just download data without uploading, or uploading an existing manifest. As of the 2.0 release, the program
has expanded functionality which includes the ability to incorporate new data sources, manipulate pre-existing subject metadata,
and aggregate classifications from Zooniverse data exports.

## Getting Started
### Prerequisites
* Valid Zooniverse login credentials, contributor access to an existing project. 
* Python 3.9+ (Tested thoroughly on 3.9, report issues with higher versions via GitHub)
* Current [Requirements](https://github.com/coolneighbors/unWISE-verse/blob/main/requirements.txt)
### Installation
* Clone the git repository at github.com/coolneighbors/unWISE-verse:

```
git clone http://github.com/coolneighbors/unWISE-verse
```

* Install the necessary requirements:
```
pip install requirements.txt
```

Alternatively, you can directly install both using:
```
pip install git+https://github.com/coolneighbors/unWISE-verse.git
```

### Execution

Using an Integrated Development Environment (IDE) or a similar program, navigate to the main.py file located in the unWISE-verse
directory. Run the main.py file in order to start the program and interact with the user interface.

If you use the command line/powershell for python, set your current directory to the unWISE-verse directory and run the command:
```
python main.py
```

### Usage

#### Logging In
Upon running the program for the first time, the user will be greeted by a window requesting login information. This is 
your Zooniverse username and password, for the purposes of interacting with the Zooniverse API. This information is encrypted locally, and saved locally
if the 'Remember Me' option is selected in the login window. If necessary, delete the 'saved_session.pickle' file as this contains 
all the cached information about your encrypted login details and other saved selections in the interface.

#### Session Selection
After logging in, the user is presented with a session selection screen. 

As of version 2.0, there are the following options:
- Pipeline: Generate manifests and upload them to Zooniverse 
- Manipulation: Collect subject information from Zooniverse and manipulate their metadata
- Classification: Generate aggregated classifications using classification and workflow Zooniverse data exports

#### Using the Pipeline Session
unWISE-verse, by default, supports the following subclasses of AstronomyDatasets:
- Cool Neighbors: Download data from the unWISE catalog using the WiseView API, perform post-processing scaling and grid generation, and upload to Zooniverse.
- Exoasteroids: Download both regular and difference imaging from the unWISE catalog using the WiseView API, perform post-processing scaling, grid generation and image combination, and upload to Zooniverse.
- Legacy Survey: Download data from the Legacy Survey API and upload to Zooniverse.

To implement a new subclass of AstronomyDataset, see the [full guide](ImplementingAstronomyDatasetSubclass.md) for more details.

The Pipeline session has three actions the user can perform:
- Manifest: Download data using the currently selected AstronomyDataset type (see above), perform post-processing scaling and grid generation (if implemented in the current AstronomyDataset type), and save the data/metadata to a manifest file.
- Upload: Upload the data/metadata from a manifest file to a Zooniverse subject set.
- Full: Perform both the Manifest and Upload actions in sequence.

Manifest Requirements:
- Target List Filename: A CSV file containing the target list for the current AstronomyDataset type. The CSV file should contain the following columns: "ra", "dec", and any additional columns for metadata. Other required columns can be defined in the subclass implementation.
- Manifest Filename: The name of the manifest file to save the data/metadata to.
- PNG Directory: The directory to save the PNG images to.
- Dataset Type: The subclass of AstronomyDataset to use for the download process and metadata formatting.
- Metadata: Additional options for the metadata formatting and image manipulation, such as grid generation and scaling.

Upload Requirements:
- Manifest Filename: The name of the manifest file to upload the data/metadata from.
- Project ID: The ID of the Zooniverse project to upload the data to.
- Subject Set ID: The ID of the Zooniverse subject set to upload the data to.

##### How to Format a Target List CSV File
The exact implementation of the target list CSV file is dependent on the subclass of AstronomyDataset being used. The Cool Neighbors subclass requires the following columns in the Target List CSV file:
- RA: The right ascension of the target in decimal degrees.
- DEC: The declination of the target in decimal degrees.
- Target ID: An integer identifier for the target.
- BITMASK: A bitmask value for the target, to identify the type of target.

However, the Cool Neighbors subclass requires more columns than what is listed here (see Dataset.py file). This is because the remainder of 
the columns are automatically populated through the mutable columns via the user interface. The user interface will 
populate the remaining columns with the values input by the user (or the default values set in the UserInterface variables
if the user does not change anything). As a rule of thumb, metadata is either populated via the Target List CSV file or 
the user interface as a mutable column.

The Exoasteroids subclass requires the following columns in the Target List CSV file:
- RA: The right ascension of the target in decimal degrees.
-  DEC: The declination of the target in decimal degrees.
- Target ID: An integer identifier for the target.
- BITMASK: A bitmask value for the target, to identify the type of target.

The Legacy Survey subclass requires the following columns in the Target List CSV file:
- RA: The right ascension of the target in decimal degrees.
- DEC: The declination of the target in decimal degrees.
- Target ID: An integer identifier for the target.

##### Common Mutable Metadata
The user interface will automatically populate the mutable columns with the values input by the user (or the default values set in the UserInterface variables).
Some common mutable columns include:
- FOV: The field of view of the image in arcseconds.
- Grid Count: The number of grid squares to span across the image.
- Grid Color: The color of the grid lines in the image.
- Add Grid: Whether to include grid lines in the image.
- Grid Type: The type of grid to include in the image (Solid, Intersection, or Dashed).
- Minbright: The minimum brightness value for the image. (Optional, can be set to dynamic by leaving the field blank)
- Maxbright: The maximum brightness value for the image. (Optional, can be set to dynamic by leaving the field blank)
- Scale Factor: The scaling factor for the image.
- Ignore Partial Cutouts: Whether to ignore partial cutouts in the image or incomplete data.
- Select Image Type: The type of image to download/construct (Regular Image, Difference Image, Both)
- Zoom: The zoom level for the image.
- Layer: The primary data layer to display.
- Blink: The secondary blink data layer to display.

#### Using the Manipulation Session
The Manipulation session allows the user to collect subject information from Zooniverse and manipulate their metadata. The user can interact with the user interface in the following ways:
- Collect: Collect subject information from Zooniverse and save it locally for easy access.
- Delete: Delete the locally saved cache of subject information.
- Search: Search for a specific subject(s) in the locally saved cache of subject information. Searches based on subject metadata.
- Find: Find a functional search python file, used to search for subjects based on a function call which takes a dictionary representing the subject as an argument and returns a boolean value.
- Subject Selection: Select one or more subjects to perform actions on in the action menu. Left click to select one at a time. 
Shift left click between two subjects to select all subjects between them. Ctrl left click to select multiple individual subjects.
Double left click to select all subjects. Double right click to deselect all subjects. Only the topmost subject is displayed.
- Action Menu: Perform actions on the selected subjects.
    - Modify Field Name: Replace a pre-existing field name with a new field name.
      - Parameters:
        - Current Field Names: The field name(s) to replace. (Format: "field1, field2, field3")
        - New Field Names: The new field name(s) to replace the current field name(s). (Format: "newfield1, newfield2, newfield3")
    - Modify Field Value: Replace a pre-existing field value with a new field value.
        - Parameters:
          - Field Names: The field name to replace the value of. (Format: "field1", "field2", "field3")
          - New Values: The new field value(s) to replace the current field value(s). (Format: "newvalue1, newvalue2, newvalue3")
    - Remove Subjects: Remove the selected subjects from the subject set on Zooniverse. (Warning: This action is irreversible)
    - Delete Subjects: Delete the selected subjects from the project on Zooniverse. (Warning: This action is irreversible)
    - Download Subject GIF: Download the GIF of the selected subject(s) from Zooniverse
      - Parameters:
        - Download Directory: The directory to save the GIF(s) to.
        - Speed: The speed of the GIF(s) to download, in ms per frame.
- Subject Information: Display the metadata of the (topmost) selected subject or the subject's flipbook.

#### Using the Classification Session
The Classification session allows the user to generate aggregated classifications using classification and workflow Zooniverse data exports. 
In order for it to function, the user must place the 'classifications' and 'workflows' data exports (from the Zooniverse Data Exports tab) in the 
local 'ClassificationFiles' folder in the unWISE-verse directory. The user can interact with the user interface in the following ways:
- Project ID: The ID of the Zooniverse project to generate aggregated classifications for.
- Workflow ID: The ID of the Zooniverse workflow to generate aggregated classifications for.
- Workflow Min Version: The minimum version of the workflow to generate aggregated classifications from.
- Workflow Max Version: The maximum version of the workflow to generate aggregated classifications from.
- Aggregate: Generate aggregated classifications using the classification and workflow Zooniverse data exports. 
The generated files will appear in the 'ClassificationFiles' folder in the unWISE-verse directory in the corresponding project/workflow folders.
- Classify: Not yet implemented.

## Authors
Project Lead: [Aaron Meisner](https://www.linkedin.com/in/aaron-meisner/)

NOIRLab Interns: [Austin Humphreys](https://www.linkedin.com/in/austin-humphreys-b87055187/) and [Noah Schapera](https://www.linkedin.com/in/noah-schapera-86303a1b9/)

## Version History

0.1 -- Working pipeline, minimum viable product for data upload workflow.
	
	Downloads data from unWISE catologue given list of targets RA and DEC in CSV. Option to add grid lines. Uploads to zooniverse subject set.
	
	Other features: Download data without publishing. Publish data without uploading. Dynamically modify subject metadata.
	
	To Do Before Release: Add multiprocessing to data downloading. Add compatability with .fits files. Add GUI

0.2 -- Refactoring flipbooks into python package, UI improvements, multiprocessing added.

    Added: GUI -- allows user to easily input Zooniverse credentials, filenames, and project/subject set ID. 
	    Multiprocessing - significantly speeds up image download time by using multiple threads at once. 
	Refactored: flipbooks -- Transfered wv.py and related scripts to flipbooks repo. Created python package from that repo. 
	To Do: Compatability with FITS files. Make UI run throghout program rather than only at the start. Add more options for metadata.
    
1.0  -- Initial Release (July 19th, 2022)
    
    Fixed UI shutdown after program start, added metadata options for grid color, size. Added dynamic minbright/maxbright parameter selection.
    
    Updated UI color for more contrast
    
    Refactored back-end dataset creation. No longer dependent on a master header list and can be used with any set of additional metadata.
    
    Hashed wiseview / simbad / vizer links into subject metadata
    
    Updated readme with recent changes
    
    Renamed repo to unWISE-verse

2.0  -- Improved Release (August 6th, 2024)
	
	Refactored various backend systems to be more generalized for future projects, beyond the original scope of the
	Backyard Worlds: Cool Neighbors project.

	Refactored Systems:
	- Data/Datasets
	- Spout
	- Progress visualizations
	- Local session saving
    - User interface

	New/Improved features:
	- Improved failsafe measures for continuing manifest generation after fatal shutdowns
	- Added additional windows for extended utility
		- Pipeline: Generate manifests and upload them to Zooniverse
		- Manipulation: Collect subject information from Zooniverse and manipulate their metadata
		- Classification: Generate aggregated classifications using classification and workflow Zooniverse data exports
	- Progress bar: Details the current action being performed and its progress
	- Easily definable AstronomyDataset subclasses: Creating a subclass of AstronomyDataset will automatically populate the user interface
	and allows for easily implementation of new types of data requests. Notably, this extents the utility of the program well 
	beyond just interfacing with WiseView as was originally intended.
    - Improved user interface: More intuitive and user-friendly interface for the user to interact with the program.
    - Improved logging: More detailed logging of program actions and errors for easier debugging.
    - Improved error handling: More robust error handling for various program actions.
    - Improved data handling: More efficient multiprocessing for data collection and manipulation.

	
## License
Distributed under the MIT License (see LICENSE.txt)

## Acknowledgments
This pipeline is built primarily with the [WiseView API] in mind. Many thanks go to the creator and maintainers of the software. 

Caselden D., Westin P. I, Meisner A., Kuchner M. and Colin G. 2018 WiseView: Visualizing Motion and Variability of Faint WISE Sources, Astrophysics Source Code Library ascl: 1806.004

This pipeline would not have been possible without the pre-existing infrastructure established as a part of the [Panoptes-Client Zooniverse API](https://github.com/zooniverse/panoptes-python-client).

