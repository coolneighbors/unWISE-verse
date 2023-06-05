from setuptools import setup
import pip

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='unWISE-verse',
    url='https://github.com/coolneighbors/unWISE-verse.git',
    author='Aaron Meisner',
    author_email='aaron.meisner@noirlab.edu',
    packages=['unWISE-verse'],
    install_requires=requirements,
    version='1.0',
    license='MIT',
    description='An integrated unWISE data collection and Zooniverse upload pipeline using the Panoptes-Client.',
    long_description=open('README.md').read(),
)

# This is to avoid the following error: https://github.com/zooniverse/panoptes-python-client/issues/264
pip.main(['install', 'python-magic==0.4.27'])
pip.main(['uninstall', 'python-magic-bin==0.4.14'])
pip.main(['install', 'python-magic-bin==0.4.14'])