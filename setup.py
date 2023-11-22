"""Minimal setup file for Exon-Media assignment."""

from setuptools import find_packages
from distutils.core import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='ExonProject',
    version='0.1.0',
    description='Exon-Media assignment',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    package_data={
        "data.db_data": ["*.json"],
        "data.cfg_global": ["*.json"],
        "data.cfg_tests": ["*.json"],
        "data.jobs_data": ["*.*"],
    },

    # metadata
    author='Efi Ovadia',
    author_email='efovadia@gmail.com',
    license='proprietary',
    install_requires = [required, 'pytest']
)