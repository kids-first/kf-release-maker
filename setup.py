import os
from setuptools import setup, find_packages

root_dir = os.path.dirname(os.path.abspath(__file__))
req_file = os.path.join(root_dir, 'requirements.txt')
with open(req_file) as f:
    requirements = f.read().splitlines()

setup(
    name='kf-release-maker',
    version='2.0.0',
    description='Kids First software release authoring tool',
    author='Kids First Data Resource Center',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'release=kf_release_maker.cli:cli',
        ],
    },
    include_package_data=True,
    install_requires=requirements
)
