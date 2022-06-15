# FullPipeline

An integrated unWISE data collection and Zooniverse upload pipeline using the Panoptes-Client
## Description
FullPipeline allows a user to quickly download a large set of target data from the unWISE AWS and upload the data to a Zooniverse subject set. In addition, users have the option to just download data without uploading, or uploading an existing set set of target png's. 
## Getting Started
### Dependencies
* Valid Zooniverse login credentials, contributor access to an existing project. 
* Python 3.10
* Python Packages:
	* python-magic-bin
	* flipbooks
	* Panoptes-Client
	* Pillow
	* getpass
	* requests
	* os
	* shutil
	* csv
	* tkinter
### Installing
* Dowload python packages as nescessary (recommended to use pip or similar)
```
pip install panoptes-client
		Pillow
		getpass
		requests
		os
		shutil
		csv
		python-magic-bin
		git+https://github.com/coolneighbors/flipbooks.git
		tkinter

```
* Clone into git repository at github.com/coolneighbors/FullPipeline
```
git clone http://github.com/coolneighbors/FullPipeline
```

### Executing program
* FullPipeline allows the user to download and upload, just download, or just upload targets to a subject set in Zooniverse

* If you intend to download data from the unWISE catologue, this program requires a list of targets.
	* The targets should be provided in a csv file as follows:
	* Note all ra_n and dec_n should be numerical values (decimals allowed)
```
RA,DEC,!GRID
ra_1,dec_1,[1, 0, or empty]
ra_2,dec_2,[1, 0, or empty] 
ra_3,dec_3,[1, 0, or empty]
...,...
ra_n,dec_n,[1, 0, or empty]
```

The grid metadata allows the user to decide whether a grid will be overlayed onto the image downloaded from the unWISE catologue. 


* Navigate to FullPipeline directory, and in cmd/powershell enter the command
```
python ./ZooniversePipeline.py/
```
## Notes

FullPipeline uses a semi-modular metadata system. In order to add another line of metadata to the subject set, add a ![metadata] column to both the targets.csv and ![metadata] column to the second row of master_header.txt
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
* [panoptes-python-client](https://github.com/zooniverse/panoptes-python-client)
* [tkinter tutorial](https://realpython.com/python-gui-tkinter/)
* [multiprocessing tutorial](https://tutorialedge.net/python/python-multiprocessing-tutorial/)