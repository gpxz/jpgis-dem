#!/usr/bin/python
# coding: utf8


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
    py_modules=["jpgisdem"],
    install_requires=[
        "Click",
    ],
    entry_points={
        "console_scripts": [
            "jpgis-dem = jpgisdem:cli",
        ],
    },
)


# setup(
#     name="jpgis-dem",
#     version=version,
#     description="Convert JPGIS .xml DEM files to geotiffs.",
#     long_description=readme,
#     author="Andrew Nisbet",
#     author_email="andrew@gpxz.io",
#     url="https://github.com/gpxz/jpgis-dem",
#     download_url="https://github.com/gpxz/jpgis-dem",
#     license="The MIT License",
#     packages=["jpgisdem"],
#     package_data={"": ["LICENSE", "README.md"]},
#     package_dir={"jpgisdem": "jpgisdem"},
#     include_package_data=True,
#     # install_requires=requires,
#     # zip_safe=False,
#     keywords="elevation",
#     classifiers=[
#         # 'Development Status :: 5 - Production/Stable',
#         "Intended Audience :: Developers",
#         "Intended Audience :: Science/Research",
#         "License :: OSI Approved :: Apache Software License",
#         "Natural Language :: English",
#         "Operating System :: OS Independent",
#         # 'Programming Language :: Python :: 2.7',
#         # 'Programming Language :: Python :: 3.3',
#         # 'Programming Language :: Python :: 3.4',
#         # 'Programming Language :: Python :: 3.5',
#         "Topic :: Internet",
#         "Topic :: Internet :: WWW/HTTP",
#         "Topic :: Scientific/Engineering :: GIS",
#         "Topic :: Software Development :: Libraries :: Python Modules",
#     ],
# )
