import subprocess
from setuptools import setup

with open('requirements.txt', encoding="utf-16") as f:
    requirements = f.read().splitlines()

setup(
    name='unWISE_verse',
    url='https://github.com/coolneighbors/unWISE-verse.git',
    author='Aaron Meisner',
    author_email='aaron.meisner@noirlab.edu',
    packages=['unWISE_verse'],
    install_requires=requirements,
    package_data={'unWISE_verse': ['themes/awthemes-10.4.0/*']},
    version='2.0',
    license='MIT',
    description='An integrated astronomy data collection system and Zooniverse upload pipeline using the Panoptes-Client.',
    long_description=open('README.md').read(),
)

# This fixes an import bug with the python-magic and python-magic-bin packages.
# https://github.com/zooniverse/panoptes-python-client/issues/264
#import platform
#
#if platform.system() == 'Windows':
#    subprocess.call(['pip', 'install', 'python-magic'])
#    subprocess.call(['pip', 'uninstall', 'python-magic-bin'])
#    subprocess.call(['pip', 'install', 'python-magic-bin'])
