from setuptools import setup

setup(
    name='unWISE-verse',
    url='https://github.com/coolneighbors/unWISE-verse.git',
    author='Aaron Meisner',
    author_email='aaron.meisner@noirlab.edu',
    packages=['unWISE-verse'],
    install_requires=['astropy==5.3','certifi==2023.5.7','charset-normalizer==3.1.0','contourpy==1.0.7', 'cycler==0.11.0', 'flipbooks @ git+https://github.com/coolneighbors/flipbooks.git@5e85b57a5391b9e52d2b8f0ee4261a47f99e651e', 'fonttools==4.39.4', 'future==0.18.3', 'idna==3.4', 'imageio==2.30.0', 'importlib-resources==5.12.0', 'kiwisolver==1.4.4', 'matplotlib==3.7.1', 'numpy==1.24.3', 'packaging==23.1', 'panoptes-client==1.6.0', 'Pillow==9.5.0', 'pyerfa==2.0.0.3', 'pyparsing==3.0.9', 'python-dateutil==2.8.2', 'python-magic==0.4.27', 'python-magic-bin==0.4.14', 'PyYAML==6.0', 'redo==2.0.4', 'requests==2.28.2', 'six==1.16.0', 'urllib3==1.26.16'],
    version='1.0',
    license='MIT',
    description='An integrated unWISE data collection and Zooniverse upload pipeline using the Panoptes-Client.',
    long_description=open('README.md').read(),
)
