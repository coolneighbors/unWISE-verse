import subprocess
from setuptools import setup

with open('requirements.txt', encoding="utf-16") as f:
    requirements = f.read().splitlines()

# This fixes an import bug with the python-magic and python-magic-bin packages.
# https://github.com/zooniverse/panoptes-python-client/issues/264
def fix_python_magic_install_order():
    subprocess.call(['pip', 'uninstall', f'python-magic'])

    python_magic = [line for line in requirements if 'python-magic' in line]
    if(len(python_magic) != 1):
        for p in python_magic:
            if("bin" in p):
                python_magic.remove(p)
        if(len(python_magic) != 1):
            raise Exception(f'python-magic requirement not found in requirements.txt or found multiple times: \'{python_magic}\'')
    python_magic = python_magic[0]
    python_magic_version = python_magic.split('==')[1]

    if(len(python_magic_version) != 0):
        subprocess.call(['pip', 'install', f'python-magic=={python_magic_version}'])
    else:
        subprocess.call(['pip', 'install', 'python-magic'])

    python_magic_bin = [line for line in requirements if 'python-magic-bin' in line]
    if(len(python_magic_bin) != 1):
        raise Exception(f'python-magic-bin requirement not found in requirements.txt or found multiple times: \'{python_magic_bin}\'')

    python_magic_bin = python_magic_bin[0]
    python_magic_bin_version = python_magic_bin.split('==')[1]
    if(len(python_magic_bin_version) != 0):
        subprocess.call(['pip', 'uninstall', f'python-magic-bin=={python_magic_bin_version}'])
        subprocess.call(['pip', 'install', f'python-magic-bin=={python_magic_bin_version}'])
    else:
        subprocess.call(['pip', 'uninstall', 'python-magic-bin'])
        subprocess.call(['pip', 'install', 'python-magic-bin'])

    requirements.remove(python_magic)
    requirements.remove(python_magic_bin)

fix_python_magic_install_order()

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