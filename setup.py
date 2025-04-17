#!/usr/bin/python
# coding: utf8

from setuptools import find_packages
import re


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open("jpgisdem/__init__.py", "r") as f:
    version = re.search(r'^__version__ = "([\d\.]+)"', f.read(), re.MULTILINE).group(1)


if not version:
    raise RuntimeError("Cannot find version information")


with open("README.md") as f:
    readme = f.read()

setup(
    name="jpgis-dem",
    version=version,
    description="Convert JPGIS .xml DEM files to geotiffs.",
    long_description=readme,
    long_description_content_type='text/markdown',
    url="https://github.com/gpxz/jpgis-dem",
    download_url="https://github.com/gpxz/jpgis-dem",
    author="Andrew Nisbet",
    author_email="andrew@gpxz.io",
    license="The MIT License",
    package_data={"": ["LICENSE", "README.md"]},
    packages=find_packages(),
    py_modules=["jpgisdem"],
    install_requires=[
        "click",
        "lxml",
        "numpy",
        "rasterio",
    ],
    entry_points={
        "console_scripts": [
            "jpgis-dem = jpgisdem:cli",
        ],
    },
    keywords="elevation",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: GIS",
    ],
)
