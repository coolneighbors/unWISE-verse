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
```
* Clone into git repository at github.com/coolneighbors/FullPipeline
```
git clone http://github.com/coolneighbors/FullPipeline
```
* In repository, create pngs directory
```
mkdir pngs
```
### Executing program
* FullPipeline allows the user to download and upload, just download, or just upload targets to a subject set in Zooniverse

* If you intend to download data from the unWISE catologue, this program requires a list of targets.
	* The targets should be provided in a csv file as follows:
	* Note all ra_n and dec_n should be numerical values (decimals allowed)
```
RA,DEC
ra_1,dec_1
ra_2,dec_2
ra_3,dec_3
...,...
ra_n,dec_n
```

* Navigate to FullPipeline directory, and in cmd/powershell enter the command
```
python ./PipelineStart.py/
```

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

TO DO

## License

UNKNOWN -- Aaron?

## Acknowledgments
* [panoptes-python-client](https://github.com/zooniverse/panoptes-python-client)