# ZPipe

An integrated unWISE data collection and Zooniverse upload pipeline using the Panoptes-Client
## Description
ZPipe allows a user to quickly download a large set of target data from the WiseView server and upload the data to a Zooniverse subject set. In addition, users have the option to just download data without uploading, or uploading an existing set set of target png's. 
## Getting Started
### Dependencies
* Valid Zooniverse login credentials, contributor access to an existing project. 
* Python 3.10
* Python Packages:
	* python-magic-bin
	* flipbooks
	* Panoptes-Client
	* Pillow
	* requests
	* os
	* shutil
	* csv
	* tkinter
	* datetime
### Installing
* Dowload python packages as nescessary (recommended to use pip install or similar)
``` 
panoptes-client
Pillow
requests
csv
git+https://github.com/coolneighbors/flipbooks.git
tk
python-magic-bin
```
* Clone into git repository at github.com/coolneighbors/ZPipe
```
git clone http://github.com/coolneighbors/ZPipe
```

### Executing program
* ZPipe allows the user to download and upload, just download, or just upload targets to a subject set in Zooniverse

* If you intend to download data from the unWISE catologue, this program requires a list of targets.
	* The targets should be provided in a csv file as follows:
	* Note all ra_n and dec_n should be numerical values (decimals allowed)
        * Unique metadata for each target should be added in subsequent columns, along with a header. This header does not need to be "unique_metadata" and should be a label that describes the metadata being added to each target. For example, notes for each target may be added under a "Notes" column
        * To make a set of metadata private or prevent zooniverse users from accessing data under a header, use a "!" or "#" tag. For more details, see the Zooniverse guide on metadata visibility.
```
RA,DEC,unique_metadata
ra_1,dec_1,metadata1
ra_2,dec_2,metadata2
ra_3,dec_3,metadata3
...,...
ra_n,dec_n,metadataN
```

* Navigate to FullPipeline directory, and in cmd/powershell enter the command
```
python main.py
```

Select desired program behavior using the bottom row of buttons.

Enter the required fields for zooniverse and or file information.

You can change the size, FOV, post processing effects, and image parameters by changing options under the "metadata" option. 

* If you would like to rescale the image, click the metadata button and input an integer scaling factor (default is 1)

* If you would like to add a grid to the image, click the metadata button and select "Grid"

* Change the FOV of the image by modifying the FOV field (integer inputs only)

* Change the minbright and maxbright of the image by changing the values in these respective fields. Minbright sets all pixel values below a set luminosity (in vega nmags) to black, while maxbright sets all pixel values above a set luminosity (in vega nmags). Pixel values in between these min/maxbright parameters are assigned to a gray value by a linear stretch between the min and maxbright parameters. 

Select "Print progress" to view program progess. Do not change this selection after hitting submit and before program has completed. 

When all selections have been made and fields are entered, hit "Submit"

## Notes

ZPipe uses a semi-modular metadata system. In order to add another line of metadata to the subject set, add a ![metadata] column to the second row of master_header.txt
Failure to do so will result in an error message.

You can turn off cross-checking with a master_header.txt file by changing the enable_strict_manifest field in the generate_manifest function of spout.py to false. This is not recommended.

The master_header.txt file has the following format:

*Assuming a delimiter of " "*
```
DataFieldName1 DataFieldName2 DataFieldName3 ...
MetadataFieldName1 MetadataFieldName2 MetadataFieldName3 ...
```
The number of data field names and metadata field names does **not** need to match.

## Help

In the UI, select the [Help] button to view instructions on program operation. The following text will appear in a popup window.

How to use: Select pipeline mode using top row of buttons. 
	* Generate a manifest / data without publishing - [manifest] 
	* Upload an existing manifest and data to zooniverse -[upload]
	* Run the whole pipeline to generate a manifest / data from target list and upload to zooniverse -[full]

For 
 [manifest]  : Only target filename and manifest filename field are required.
 [upload] : Only username, password, project ID, subject set ID, and manifest filename are required
 [full] : All fields are required.



## Authors
[Noah Schapera](https://www.linkedin.com/in/noah-schapera-86303a1b9/)
[Austin Humphreys](https://www.linkedin.com/in/austin-humphreys-b87055187/)
[Aaron Meisner](https://www.linkedin.com/in/aaron-meisner/)


## Version History

0.1 -- Working pipeline, minimum viable product for data upload workflow. Not quite ready for release
	
	Downloads data from unWISE catologue given list of targets RA and DEC in CSV. Option to add grid lines. Uploads to zooniverse subject set.
	
	Other features: Download data without publishing. Publish data without uploading. Dynamically modify subject metadata.
	
	To Do Before Release: Add multiprocessing to data downloading. Add compatability with .fits files. Add GUI

0.2 -- Refactoring flipbooks into python package, UI improvements, multiprocessing added.

    Added: GUI -- allows user to easily input Zooniverse credentials, filenames, and project/subject set ID. 
	    Multiprocessing - significantly speeds up image download time by using multiple threads at once. 
	Refactored: flipbooks -- Transfered wv.py and related scripts to flipbooks repo. Created python package from that repo. 
	To Do: Compatability with FITS files. Make UI run throghout program rather than only at the start. Add more options for metadata.
	
## License

Distributed under the MIT License (see LICENSE.txt)

## Acknowledgments
This pipeline is built on the WiseView platform.

Caselden D., Westin P. I, Meisner A., Kuchner M. and Colin G. 2018 WiseView: Visualizing Motion and Variability of Faint WISE Sources, Astrophysics Source Code Library ascl: 1806.004

* [panoptes-python-client](https://github.com/zooniverse/panoptes-python-client)
* [tkinter tutorial](https://realpython.com/python-gui-tkinter/)
* [multiprocessing tutorial](https://tutorialedge.net/python/python-multiprocessing-tutorial/)
