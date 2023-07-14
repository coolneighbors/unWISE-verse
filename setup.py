from setuptools import setup

with open('requirements.txt', encoding="utf-16") as f:
    requirements = f.read().splitlines()
    print(requirements)

setup(
    name='unWISE_verse',
    url='https://github.com/coolneighbors/unWISE-verse.git',
    author='Aaron Meisner',
    author_email='aaron.meisner@noirlab.edu',
    packages=['unWISE_verse'],
    install_requires=requirements,
    version='1.2',
    license='MIT',
    description='An integrated unWISE data collection and Zooniverse upload pipeline using the Panoptes-Client.',
    long_description=open('README.md').read(),
)