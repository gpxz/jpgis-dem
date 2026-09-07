import hashlib
import os
import shutil

import numpy as np
import pytest
import rasterio

import jpgisdem

XML_PATH = "tests/data/FG-GML-3926-76-DEM10B-20161001.xml"
SINGLE_ZIP_PATH = "tests/data/FG-GML-3926-76-DEM10B.zip"
MULTI_ZIP_PATH = "tests/data/FG-GML-3624-30-DEM5B.zip"
NEW_XML_PATH = "tests/data/FG-GML-4530-77-05-DEM1A-20260522.xml"

TMP_DIR = "tests/data/tmp"


@pytest.fixture()
def tidy_tmp_dir():
    os.makedirs(TMP_DIR, exist_ok=True)
    yield
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)


class TestXML2TIF:
    def test_xml_file(self, tidy_tmp_dir):
        dst_path = os.path.join(TMP_DIR, "out.tif")
        with open(XML_PATH) as src, open(dst_path, "wb") as dst:
            jpgisdem._xml2tif(src, dst)
        assert os.path.exists(dst_path)

    def test_new_xml_file(self, tidy_tmp_dir):
        dst_path = os.path.join(TMP_DIR, "out.tif")
        with open(NEW_XML_PATH) as src, open(dst_path, "wb") as dst:
            jpgisdem._xml2tif(src, dst)
        assert os.path.exists(dst_path)

    def test_zip_file(self, tidy_tmp_dir):
        dst_path = os.path.join(TMP_DIR, "out.tif")
        with open(SINGLE_ZIP_PATH) as src, open(dst_path, "wb") as dst:
            jpgisdem._xml2tif(src, dst)
        assert os.path.exists(dst_path)

    def test_xml_zip_file_equivalence(self, tidy_tmp_dir):
        dst_xml_path = os.path.join(TMP_DIR, "out.xml.tif")
        dst_zip_path = os.path.join(TMP_DIR, "out.zip.tif")
        with open(XML_PATH) as src, open(dst_xml_path, "wb") as dst:
            jpgisdem._xml2tif(src, dst)
        with open(SINGLE_ZIP_PATH) as src, open(dst_zip_path, "wb") as dst:
            jpgisdem._xml2tif(src, dst)
        assert os.path.exists(dst_xml_path)
        assert os.path.exists(dst_zip_path)

        with open(dst_xml_path, "rb") as f:
            xml_hash = hashlib.md5(f.read()).hexdigest()
        with open(dst_zip_path, "rb") as f:
            zip_hash = hashlib.md5(f.read()).hexdigest()
        assert xml_hash == zip_hash

    def test_multi_zip(self, tidy_tmp_dir):
        dst_path = os.path.join(TMP_DIR, "out2.tif")
        with open(MULTI_ZIP_PATH) as src, open(dst_path, "wb") as dst:
            jpgisdem._xml2tif(src, dst)
        with rasterio.open(dst_path) as f:
            assert f.width == 675
            assert f.height == 450
            a = f.read(1)
            assert np.isfinite(a).sum() > 0
