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

To have more control over the output tif, you can make a json file of parameters to be passed to rasterio

```json
# profile.json
{
    "compress": "zstd",
    "zstd_level": 1,
    "blockxsize": 2048,
    "blockysize": 2048
}
```

then pass that path as `--raster-profile`

```bash
jpgis-dem xml2tif --raster-profile profile.json FG-GML-3624-31-DEM5B.zip 3624-31.geotiff
```

Keys set to `null` will be removed from the default profile, which is


```json
DEFAULT_RASTER_PROFILE = {
    "count": 1,
    "driver": "GTiff",
    "dtype": "float32",
    "compress": "deflate",
    "tiled": true,
    "blockxsize": 512,
    "blockysize": 512,
    "interleave": "pixel",
    "nodata": -9999,
}
```
