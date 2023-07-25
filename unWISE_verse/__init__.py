"""
unWISE_verse
=========

A pipeline for downloading, modifying, and uploading unWISE images to Zooniverse.

"""

import subprocess
# This fixes an import bug with the python-magic and python-magic-bin packages.
# https://github.com/zooniverse/panoptes-python-client/issues/264
subprocess.call(['pip', 'uninstall', 'python-magic-bin'])
subprocess.call(['pip', 'install', 'python-magic-bin'])
