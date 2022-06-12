# FullPipeline

An integrated unWISE data collection and Zooniverse upload pipeline using the Panoptes-Client
## Description
FullPipeline allows a user to quickly download a large set of target data from the unWISE AWS and upload the data to a Zooniverse subject set. In addition, users have the option to just download data without uploading, or uploading an existing set set of target png's. 
## Getting Started
### Dependencies
* Valid Zooniverse login credentials, contributor access to an existing project. 
* Python 3.10
* Python Packages:
	* Panoptes-Client
	* Pillow
	* getpass
	* requests
	* os
	* shutil
	* csv
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
python ./PipelineStart.py/
```
## Notes

FullPipeline uses a semi-modular metadata system. In order to add another line of metadata to the subject set, add a ![metadata] column to both the targets.csv and ![metadata] column to the second row of master_header.txt
Failure to do so will result in an error message.

You can turn off cross checking master-header by changing the enable_strict_manifest field in the generate_manifest function of spout.py to false. This is not reccomended.

## Help

We need to make a helper command! This section is reserved for that.
```
command to run if program contains helper info
```

## Authors
[Noah Schapera](https://www.linkedin.com/in/noah-schapera-86303a1b9/)
[Austin Humphreys](https://www.linkedin.com/in/austin-humphreys-b87055187/)
[Aaron Meisner](https://www.linkedin.com/in/aaron-meisner/)


## Version History

0.1 -- Working pipeline, minimum viable product for data upload workflow. Not quite ready for release
	
	Downloads data from unWISE catologue given list of targets RA and DEC in CSV. Option to add grid lines. Uploads to zooniverse subject set.
	
	Other features: Download data without publishing. Publish data without uploading. Dynamically modify subject metadata.
	
	To Do Before Release: Add multiprocessing to data downloading. Add compatability with .fits files. Add GUI

## License

Distributed under the MIT License (see LICENSE.txt)

## Acknowledgments
* [panoptes-python-client](https://github.com/zooniverse/panoptes-python-client)