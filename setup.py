from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='unWISE-verse',
    url='https://github.com/coolneighbors/unWISE-verse.git',
    author='Aaron Meisner',
    author_email='aaron.meisner@noirlab.edu',
    packages=['unWISE-verse'],
    install_requires=requirements,
    version='1.1',
    license='MIT',
    description='An integrated unWISE data collection and Zooniverse upload pipeline using the Panoptes-Client.',
    long_description=open('README.md').read(),
)