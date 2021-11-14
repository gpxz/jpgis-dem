# JPGIS DEM tool

A CLI tool to convert Japanese DEM XML files into Geotifs. A Python port of [tmizu23/demtool](https://github.com/tmizu23/demtool).

## Installation

Install with pip

```bash
pip install jpgis-dem
```


## Usage

Convert a single xml file 

```bash
jpgis-dem xml2tif FG-GML-3622-57-DEM10B-20190510.xml 3622-57.geotiff
```


Convert a 10m zip containing a single xml file

```bash
jpgis-dem xml2tif FG-GML-3622-57-DEM10B.zip 3622-57.geotiff
```


Convert a 5m zip containing multiple xml files into a merged geotiff

```bash
jpgis-dem xml2tif FG-GML-3624-31-DEM5B.zip 3624-31.geotiff
```