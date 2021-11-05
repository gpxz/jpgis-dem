import click
import numpy as np
import rasterio
from lxml import etree

# from rasterio.coords import BoundingBox
# from rasterio.crs import CRS


__version__ = "0.0.1"

NODATA_VALUE = -9999.0

COG_PROFILE = {
    "count": 1,
    "driver": "GTiff",
    "dtype": np.float32,
    "compress": "deflate",
    "tiled": True,
    "blockxsize": 512,
    "blockysize": 512,
    "interleave": "pixel",
}


def _load_xml(fh):
    try:
        tree = etree.parse(fh)
        root = tree.getroot()

        # Remove namespace.
        # From https://stackoverflow.com/questions/18159221/remove-namespace-and-prefix-from-xml-in-python-using-lxml
        for elem in root.getiterator():

            # Skip comments and processing instructions, because they do not have names.
            if not (
                isinstance(elem, etree._Comment)
                or isinstance(elem, etree._ProcessingInstruction)
            ):
                # Remove a namespace URI in the element's name
                elem.tag = etree.QName(elem).localname

        # Remove unused namespace declarations
        etree.cleanup_namespaces(root)

        return root

    except Exception as e:
        raise click.ClickException(
            f"Unable to parse '{fh.name}'. Is it a valid xml file?"
        )


def _parse_crs(root):
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
    try:
        gml_data = root.xpath("DEM/coverage/rangeSet/DataBlock/tupleList")[0].text
        tuple_strings = gml_data.strip().split("\n")
        data_strings = [t.split(",")[-1] for t in tuple_strings]
        data = np.array(data_strings, dtype=np.float32)
    except Exception as e:
        raise click.ClickException("Unable to parse main data.")
    return data


def _merge_data(start_data, main_data, height, width):
    # Merge.
    data = np.concatenate([start_data, main_data])

    # Handle NODATA.
    data[data == NODATA_VALUE] = np.nan

    # Reshape to square.
    n_cells = height * width
    if not n_cells == len(data):
        raise click.ClickException(
            f"Data size {len(data)} doesn't match desired size {n_cells}"
        )
    array = data.reshape((height, width))

    return array


def _rasterize(src_file, dst_file):
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
def rasterize(src_file, dst_file):
    _rasterize(src_file, dst_file)


cli.add_command(rasterize)
