import os
import random
import shutil
import string
import tempfile
import zipfile

import click
import numpy as np
import rasterio
import rasterio.merge
from lxml import etree

__version__ = "0.0.7"


# NODATA seems to be -9999 for all DEMs. A more advanced (but slower) way to
# handle this would be to parse the japanese text NODATA flag on each cell.
NODATA_VALUE = -9999.0


# Save output as a compressed cloud-optimised geotiff.
COG_PROFILE = {
    "count": 1,
    "driver": "GTiff",
    "dtype": np.float32,
    "compress": "deflate",
    "tiled": True,
    "blockxsize": 512,
    "blockysize": 512,
    "interleave": "pixel",
    "nodata": NODATA_VALUE,
}


def _random_string(n=16):
    return "".join(random.choices(string.ascii_lowercase, k=n))


def _tmp_path(tmp_folder, extension=""):
    if extension and not extension.startswith("."):
        extension = "." + extension
    os.makedirs(tmp_folder, exist_ok=True)
    filename = _random_string(16) + extension
    path = os.path.join(tmp_folder, filename)
    return path


def _load_xml(fh):
    """Parse the xml file.

    Args:
        fh: File handle to an xml file (for a zipped xml file).

    Returns:
        root: Root node of ElementTree.
    """
    try:

        # For zip files, parse the first file in the zipped directory.
        # if fh.name.lower().endswith(".zip"):
        #     archive = zipfile.ZipFile(fh)
        #     items = archive.namelist()[0]
        #     with archive.open(items) as fhz:
        #         tree = etree.parse(fhz, parser=etree.XMLParser(huge_tree=True))
        # else:
        tree = etree.parse(fh, parser=etree.XMLParser(huge_tree=True))

        root = tree.getroot()

        # Remove namespace.
        # From https://stackoverflow.com/questions/18159221/remove-namespace-and-prefix-from-xml-in-python-using-lxml
        for elem in root.getiterator():
            if not (
                isinstance(elem, etree._Comment)
                or isinstance(elem, etree._ProcessingInstruction)
            ):
                elem.tag = etree.QName(elem).localname
        etree.cleanup_namespaces(root)

        return root

    except Exception as e:
        raise click.ClickException(
            f"Unable to parse '{fh.name}'. Is it a valid xml file?"
        )


def _parse_crs(root):
    """Find the coordinate system on the xml.

    DEM files are either jgd2011 or jgd2000 (which are similar within a few metres for Japan).

    Args:
        root: ElementTree of xml document.

    Returns:
        crs: rasterio CRS object.
    """
    try:
        gml_srs = root.xpath("DEM/coverage/boundedBy/Envelope/@srsName")[0]
    except IndexError:
        raise click.ClickException("Unable to find srs. Is this a JPGIS GML DEM file?")

    if gml_srs == "fguuid:jgd2011.bl":
        epsg = 6668
    elif gml_srs == "fguuid:jgd2000.bl":
        epsg = 4612
    else:
        raise click.ClickException(f"Unsupported srs: '{gml_srs}'.")

    crs = rasterio.crs.CRS.from_epsg(epsg)

    return crs


def _parse_shape(root):
    """Get the shape of the array from the xml file.

    Args:
        root: ElementTree of xml document.

    Returns:
        height, width: Ingeger shape.
    """
    try:
        gml_grid_low = root.xpath(
            "DEM/coverage/gridDomain/Grid/limits/GridEnvelope/low"
        )[0].text
        gml_grid_high = root.xpath(
            "DEM/coverage/gridDomain/Grid/limits/GridEnvelope/high"
        )[0].text
        gml_labels = root.xpath("DEM/coverage/gridDomain/Grid/axisLabels")[0].text
    except IndexError:
        raise click.ClickException("Unable to find GridEnvelope shape.")

    try:
        assert gml_labels == "x y", "Unknown format"
        xmin = int(gml_grid_low.split(" ")[0])
        ymin = int(gml_grid_low.split(" ")[1])
        xmax = int(gml_grid_high.split(" ")[0])
        ymax = int(gml_grid_high.split(" ")[1])

        assert xmin == 0
        assert ymin == 0

        width = xmax + 1 - xmin
        height = ymax + 1 - ymin
    except Exception as e:
        raise click.ClickException("Unable to parse GridEnvelope shape.")

    return height, width


def _parse_bounds(root):
    """Find the bounds of the raster, in the crs.

    Args:
        root: ElementTree of xml document.

    Returns:
        bounds: rasterio BoundingBox.
    """
    try:
        gml_lower_corner = root.xpath("DEM/coverage/boundedBy/Envelope/lowerCorner")[
            0
        ].text  # SW
        gml_upper_corner = root.xpath("DEM/coverage/boundedBy/Envelope/upperCorner")[
            0
        ].text  # NE
    except IndexError:
        raise click.ClickException("Unable to find Envelope bounds.")

    try:
        bottom = float(gml_lower_corner.split(" ")[0])
        left = float(gml_lower_corner.split(" ")[1])
        top = float(gml_upper_corner.split(" ")[0])
        right = float(gml_upper_corner.split(" ")[1])
        bounds = rasterio.coords.BoundingBox(left, bottom, right, top)
    except Exception as e:
        raise click.ClickException("Unable to parse Envelope bounds.")

    return bounds


def _load_start_data(root, height, width):
    """Load 'compressed' elevation data at the start of the array.

    When the raster starts with NULL data, this is encoded by a starting
    offset, rather than including each individual value.

    This function reads the offset and makes a NODATA array of that length.

    Args:
        root: ElementTree of xml document.

    Returns:
        data: numpy array, all NODATA values, of the appropriate length.
    """
    try:
        gml_startpoint = root.xpath(
            "DEM/coverage/coverageFunction/GridFunction/startPoint"
        )[0].text
        x_start = int(gml_startpoint.split(" ")[0])
        y_start = int(gml_startpoint.split(" ")[1])
    except Exception as e:
        raise click.ClickException("Unable to parse startPoint.")

    n_start = width * y_start + x_start
    data = np.zeros(n_start, dtype=np.float32) + NODATA_VALUE
    return data


def _load_main_data(root):
    """Load main data.

    Reads xml data line by line.

    Args:
        root: ElementTree of xml document.

    Returns:
        data: numpy array.
    """
    try:
        gml_data = root.xpath("DEM/coverage/rangeSet/DataBlock/tupleList")[0].text
        tuple_strings = gml_data.strip().split("\n")
        data_strings = [t.split(",")[-1] for t in tuple_strings]
        data = np.array(data_strings, dtype=np.float32)
    except Exception as e:
        raise click.ClickException("Unable to parse main data.")
    return data


def _merge_data(start_data, main_data, height, width):
    """Generate full 2D raster data.

    Concatenates start_data and main_data, then pads with trailing data to
    match desired shape.

    Args:
        start_data: array of any NODATA values at start of file.
        main_data: array of sunsequent values.
        height, width: raster shape.

    Returns:
        array: 2D raster data.
    """
    # Merge.
    data = np.concatenate([start_data, main_data])

    # Handle NODATA.
    data[data == NODATA_VALUE] = np.nan

    # Pad out to full size.
    n_cells = height * width
    if len(data) > n_cells:
        raise click.ClickException(
            f"Data size {len(data)} exceedes desired size {n_cells}"
        )
    if len(data) < n_cells:
        end_data = np.empty(n_cells - len(data), dtype=np.float32)
        end_data[:] = np.nan
        data = np.concatenate([data, end_data])

    # Reshape to square.
    assert len(data) == n_cells
    array = data.reshape((height, width))

    return array


def _xml2tif_single_file(src_file, dst_file):
    """Rasterise a GML xml file.

    Args:
        src_file: filehandle of xml file.
        dst_file: filehandle of geotiff to write to.
    """
    # Load file.
    root = _load_xml(src_file)

    # Parse file.
    crs = _parse_crs(root)
    height, width = _parse_shape(root)
    bounds = _parse_bounds(root)

    # Load data.
    start_data = _load_start_data(root, height, width)
    main_data = _load_main_data(root)

    # Reshape data into a 2d array.
    array = _merge_data(start_data, main_data, height, width)
    del start_data, main_data

    # Save as tif.
    transform = rasterio.transform.from_bounds(
        bounds.left, bounds.bottom, bounds.right, bounds.top, width, height
    )
    with rasterio.open(
        dst_file,
        "w",
        width=width,
        height=height,
        crs=crs,
        transform=transform,
        **COG_PROFILE,
    ) as f:
        f.write(array, 1)


@click.group()
def cli():
    pass


@click.command()
@click.argument("src_file", type=click.File("rb"))
@click.argument("dst_file", type=click.File("wb"))
def xml2tif(src_file, dst_file):
    _xml2tif(src_file, dst_file)


def _xml2tif(src_file, dst_file):

    # If xml, parse as normal.
    if not src_file.name.lower().endswith(".zip"):
        return _xml2tif_single_file(src_file, dst_file)

    # If single-file zip, parse as normal.
    archive = zipfile.ZipFile(src_file.name)
    items = archive.namelist()
    n_items = len(items)
    if n_items == 0:
        raise (click.ClickException("Empty zip."))
    if n_items == 1:
        with archive.open(items[0]) as fhz:
            return _xml2tif_single_file(fhz, dst_file)

    # If multiple file zip, convert each individually, then merge together.
    try:

        # Setup.
        tmp_folder = tempfile.mkdtemp()
        tif_paths = [_tmp_path(tmp_folder, ".tif") for _ in range(n_items)]

        # Build individual tmp rasters.
        for xml_path, tif_path in zip(items, tif_paths):
            with archive.open(xml_path) as fhz:
                _xml2tif_single_file(fhz, tif_path)

        # Check all have the same crs.
        epsgs = []
        for p in tif_paths:
            with rasterio.open(p) as f:
                epsgs.append(f.crs.to_epsg())
        if len(set(epsgs)) > 1:
            raise click.ClickException(
                "ZIP file contains XML rasters wih differing reference systems."
            )

        # Merge rasters.
        dest, transform = rasterio.merge.merge(tif_paths, nodata=NODATA_VALUE)
        dest = dest[0]
        with rasterio.open(
            dst_file,
            "w",
            width=dest.shape[1],
            height=dest.shape[0],
            crs=f"epsg:{epsgs[0]}",
            transform=transform,
            **COG_PROFILE,
        ) as f:
            f.write(dest, 1)

    finally:
        if os.path.exists(tmp_folder):
            shutil.rmtree(tmp_folder)


cli.add_command(xml2tif)
