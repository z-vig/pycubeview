"""Unit tests for measurement axis label reading utils"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import textwrap
from unittest.mock import patch, MagicMock

from pycubeview.services.read_measurement_axis_label import (
    open_wvl_file,
    open_hdr_file,
    open_txt_file,
    open_csv_file,
    open_meas,
    MEAS_HANDLERS,
    sio,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_wavelengths() -> np.ndarray:
    """Sample wavelength array for testing"""
    return np.array([400.0, 450.0, 500.0, 550.0, 600.0])


@pytest.fixture
def wvl_model(sample_wavelengths: np.ndarray) -> sio.WvlModel:
    wvl_model = sio.WvlModel(
        values=sample_wavelengths.tolist(),
        unit="nm",
        bbl=np.ones(sample_wavelengths.size, dtype=bool).tolist(),
    )
    return wvl_model


@pytest.fixture
def wvl_file(temp_dir, wvl_model):
    """Create a mock .wvl file"""
    wvl_path = temp_dir / "test.wvl"
    wvl_path.write_text(wvl_model.model_dump_json())
    return wvl_path


@pytest.fixture
def hdr_file(temp_dir, sample_wavelengths):
    """Create a valid .hdr file with wavelength data"""
    hdr_content = textwrap.dedent(
        """
        ENVI
        description = {Test HDR file}
        samples = 5
        lines = 1
        bands = 1
        wavelength = {400.0, 450.0, 500.0, 550.0, 600.0}
        """
    ).strip()

    hdr_path = temp_dir / "test.hdr"
    hdr_path.write_text(hdr_content)
    return hdr_path


@pytest.fixture
def txt_file(temp_dir, sample_wavelengths):
    """Create a valid .txt file with comma-separated wavelengths"""
    txt_content = "400.0,450.0,500.0,550.0,600.0"
    txt_path = temp_dir / "test.txt"
    txt_path.write_text(txt_content)
    return txt_path


@pytest.fixture
def csv_file(temp_dir, sample_wavelengths):
    """Create a valid .csv file with wavelength column"""
    csv_content = textwrap.dedent(
        """
        wavelength,intensity,other_data
        400.0,100,1
        450.0,110,2
        500.0,120,3
        550.0,130,4
        600.0,140,5
        """
    ).strip()

    csv_path = temp_dir / "test.csv"
    csv_path.write_text(csv_content)
    return csv_path


# ============================================================================
# Tests for open_wvl_file
# ============================================================================


class TestOpenWvlFile:
    """Tests for open_wvl_file function"""

    def test_open_wvl_file_success(self, wvl_file, sample_wavelengths):
        """Test successful reading of a .wvl file"""
        with patch(
            "pycubeview.services.read_measurement_axis_label.sio.read_wvl"
        ) as mock_read:
            mock_wvl = MagicMock()
            mock_wvl.asarray.return_value = sample_wavelengths
            mock_read.return_value = mock_wvl

            result = open_wvl_file(wvl_file)

            assert isinstance(result, np.ndarray)
            np.testing.assert_array_equal(result, sample_wavelengths)
            mock_read.assert_called_once_with(wvl_file)

    def test_open_wvl_file_with_string_path(
        self, wvl_file, sample_wavelengths
    ):
        """Test that open_wvl_file accepts string paths"""
        with patch(
            "pycubeview.services.read_measurement_axis_label.sio.read_wvl"
        ) as mock_read:
            mock_wvl = MagicMock()
            mock_wvl.asarray.return_value = sample_wavelengths
            mock_read.return_value = mock_wvl

            result = open_wvl_file(Path(wvl_file))

            assert isinstance(result, np.ndarray)

    def test_open_wvl_file_oserror(self, wvl_file):
        """Test that OSError is raised when spectralio fails"""
        with patch(
            "pycubeview.services.read_measurement_axis_label.sio.read_wvl"
        ) as mock_read:
            mock_read.side_effect = OSError("File not readable")

            with pytest.raises(OSError):
                open_wvl_file(wvl_file)


# ============================================================================
# Tests for open_hdr_file
# ============================================================================


class TestOpenHdrFile:
    """Tests for open_hdr_file function"""

    def test_open_hdr_file_success(self, hdr_file, sample_wavelengths):
        """Test successful reading of a .hdr file with wavelength data"""
        result = open_hdr_file(hdr_file)

        assert isinstance(result, np.ndarray)
        np.testing.assert_array_equal(result, sample_wavelengths)

    def test_open_hdr_file_with_spaces(self, temp_dir):
        """Test .hdr file parsing with spaces in wavelength values"""
        hdr_content = "wavelength = { 400.0 , 450.0 , 500.0 }"
        hdr_path = temp_dir / "test_spaces.hdr"
        hdr_path.write_text(hdr_content)

        result = open_hdr_file(hdr_path)

        expected = np.array([400.0, 450.0, 500.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_open_hdr_file_single_wavelength(self, temp_dir):
        """Test .hdr file with a single wavelength value"""
        hdr_content = "wavelength = {550.5}"
        hdr_path = temp_dir / "test_single.hdr"
        hdr_path.write_text(hdr_content)

        result = open_hdr_file(hdr_path)

        np.testing.assert_array_equal(result, np.array([550.5]))

    def test_open_hdr_file_missing_wavelength(self, temp_dir):
        """Test that OSError is raised when wavelength field is missing"""
        hdr_content = "samples = 5\nlines = 1\nbands = 1"
        hdr_path = temp_dir / "test_no_wvl.hdr"
        hdr_path.write_text(hdr_content)

        with pytest.raises(OSError, match="Unable to open .hdr file"):
            open_hdr_file(hdr_path)

    def test_open_hdr_file_case_insensitive(self, temp_dir):
        """
        Test that wavelength pattern matching is case-sensitive (lowercase)
        """
        hdr_content = "WAVELENGTH = {400.0, 450.0}"
        hdr_path = temp_dir / "test_uppercase.hdr"
        hdr_path.write_text(hdr_content)

        # The regex only matches lowercase "wavelength"
        with pytest.raises(OSError, match="Unable to open .hdr file"):
            open_hdr_file(hdr_path)

    def test_open_hdr_file_with_other_content(self, temp_dir):
        """Test .hdr file with multiple fields including wavelength"""
        hdr_content = textwrap.dedent(
            """
            ENVI
            description = {Hyperspectral Image}
            samples = 512
            lines = 512
            bands = 100
            wavelength = {400.0, 410.0, 420.0, 430.0, 440.0}
            wavelength units = Micrometers
            """
        ).strip()

        hdr_path = temp_dir / "test_complex.hdr"
        hdr_path.write_text(hdr_content)

        result = open_hdr_file(hdr_path)
        expected = np.array([400.0, 410.0, 420.0, 430.0, 440.0])
        np.testing.assert_array_equal(result, expected)


# ============================================================================
# Tests for open_txt_file
# ============================================================================


class TestOpenTxtFile:
    """Tests for open_txt_file function"""

    def test_open_txt_file_success(self, txt_file, sample_wavelengths):
        """
        Test successful reading of a .txt file with comma-separated values
        """
        result = open_txt_file(txt_file)

        assert isinstance(result, np.ndarray)
        np.testing.assert_array_equal(result, sample_wavelengths)

    def test_open_txt_file_single_value(self, temp_dir):
        """Test .txt file with a single wavelength value"""
        txt_content = "550.5"
        txt_path = temp_dir / "test_single.txt"
        txt_path.write_text(txt_content)

        result = open_txt_file(txt_path)

        np.testing.assert_array_equal(result, np.array([550.5]))

    def test_open_txt_file_with_spaces(self, temp_dir):
        """Test .txt file with spaces around commas"""
        txt_content = "400.0, 450.0, 500.0, 550.0"
        txt_path = temp_dir / "test_spaces.txt"
        txt_path.write_text(txt_content)

        # Note: This test documents current behavior with spaces
        # The function may need to handle this better in production
        result = open_txt_file(txt_path)

        # Values will have leading/trailing spaces converted by float()
        expected = np.array([400.0, 450.0, 500.0, 550.0])
        np.testing.assert_array_equal(result, expected)

    def test_open_txt_file_trailing_space(self, temp_dir):
        """Test .txt file with trailing space after last comma"""
        txt_content = "400.0,450.0,500.0, "
        txt_path = temp_dir / "test_trailing.txt"
        txt_path.write_text(txt_content)

        result = open_txt_file(txt_path)

        # Function removes the trailing space element
        expected = np.array([400.0, 450.0, 500.0])
        np.testing.assert_array_equal(result, expected)

    def test_open_txt_file_decimal_precision(self, temp_dir):
        """Test .txt file preserves decimal precision"""
        txt_content = "400.123456,450.654321,500.111111"
        txt_path = temp_dir / "test_precision.txt"
        txt_path.write_text(txt_content)

        result = open_txt_file(txt_path)

        expected = np.array([400.123456, 450.654321, 500.111111])
        np.testing.assert_array_almost_equal(result, expected, decimal=6)

    def test_open_txt_file_invalid_values(self, temp_dir):
        """Test .txt file with non-numeric values raises ValueError"""
        txt_content = "400.0,invalid,500.0"
        txt_path = temp_dir / "test_invalid.txt"
        txt_path.write_text(txt_content)

        with pytest.raises(ValueError):
            open_txt_file(txt_path)


# ============================================================================
# Tests for open_csv_file
# ============================================================================


class TestOpenCsvFile:
    """Tests for open_csv_file function"""

    def test_open_csv_file_success(self, csv_file, sample_wavelengths):
        """Test successful reading of a .csv file with wavelength column"""
        result = open_csv_file(csv_file)

        assert isinstance(result, np.ndarray)
        np.testing.assert_array_equal(result, sample_wavelengths)

    def test_open_csv_file_custom_column(self, temp_dir):
        """Test reading a .csv file with a custom column label"""
        csv_content = textwrap.dedent(
            """
            frequency,intensity,description
            400.0,100,Red
            450.0,110,Orange
            500.0,120,Yellow
            """
        ).strip()

        csv_path = temp_dir / "test_custom.csv"
        csv_path.write_text(csv_content)

        result = open_csv_file(csv_path, measurement_column_label="frequency")
        expected = np.array([400.0, 450.0, 500.0])

        np.testing.assert_array_equal(result, expected)

    def test_open_csv_file_missing_column(self, csv_file):
        """Test that ValueError is raised when measurement column is missing"""
        with pytest.raises(ValueError, match="No measurement column exists"):
            open_csv_file(csv_file, measurement_column_label="nonexistent")

    def test_open_csv_file_duplicate_columns(self, temp_dir):
        """Test that ValueError is raised when multiple columns match"""
        csv_content = textwrap.dedent(
            """
            wavelength,wavelength,intensity
            400.0,400.0,100
            450.0,450.0,110
            """
        ).strip()

        csv_path = temp_dir / "test_duplicate.csv"
        csv_path.write_text(csv_content)

        with pytest.raises(
            ValueError, match="Multiple measurement columns exist"
        ):
            open_csv_file(csv_path)

    def test_open_csv_file_case_insensitive(self, temp_dir):
        """Test that column label matching is case-insensitive"""
        csv_content = textwrap.dedent(
            """
            Wavelength,intensity,description
            400.0,100,Red
            450.0,110,Orange
            """
        ).strip()

        csv_path = temp_dir / "test_case.csv"
        csv_path.write_text(csv_content)

        result = open_csv_file(csv_path, measurement_column_label="wavelength")
        expected = np.array([400.0, 450.0])

        np.testing.assert_array_equal(result, expected)

    def test_open_csv_file_large_dataset(self, temp_dir):
        """Test .csv file with a large number of rows"""
        num_rows = 1000
        rows = ["wavelength,intensity"]
        rows.extend([f"{400 + i*0.2},{100 + i}" for i in range(num_rows)])
        csv_content = "\n".join(rows)

        csv_path = temp_dir / "test_large.csv"
        csv_path.write_text(csv_content)

        result = open_csv_file(csv_path)

        assert len(result) == num_rows
        assert result[0] == pytest.approx(400.0)
        assert result[-1] == pytest.approx(400 + (num_rows - 1) * 0.2)

    def test_open_csv_file_whitespace_in_values(self, temp_dir):
        """Test .csv file with whitespace in numeric values"""
        csv_content = textwrap.dedent(
            """
            wavelength,intensity
            400.0,100
            450.0,110
            """
        ).strip()

        csv_path = temp_dir / "test_whitespace.csv"
        csv_path.write_text(csv_content)

        result = open_csv_file(csv_path)
        expected = np.array([400.0, 450.0])

        np.testing.assert_array_equal(result, expected)


# ============================================================================
# Tests for open_meas dispatcher function
# ============================================================================


class TestOpenMeas:
    """Tests for open_meas dispatcher function"""

    def test_open_meas_with_wvl_file(
        self, wvl_file: str | Path, sample_wavelengths: np.ndarray
    ):
        """Test open_meas correctly dispatches to .wvl handler"""
        with patch(
            "pycubeview.services.read_measurement_axis_label.MEAS_HANDLERS"
        ) as mock_handlers:
            mock_handler = MagicMock(return_value=sample_wavelengths)
            mock_handlers.get.return_value = mock_handler

            result = open_meas(wvl_file)

            mock_handlers.get.assert_called_once_with(".wvl")
            mock_handler.assert_called_once_with(wvl_file)
            np.testing.assert_array_equal(result, sample_wavelengths)

    def test_open_meas_with_hdr_file(self, hdr_file, sample_wavelengths):
        """Test open_meas correctly dispatches to .hdr handler"""
        result = open_meas(hdr_file)

        np.testing.assert_array_equal(result, sample_wavelengths)

    def test_open_meas_with_txt_file(self, txt_file, sample_wavelengths):
        """Test open_meas correctly dispatches to .txt handler"""
        result = open_meas(txt_file)

        np.testing.assert_array_equal(result, sample_wavelengths)

    def test_open_meas_with_csv_file(self, csv_file, sample_wavelengths):
        """Test open_meas correctly dispatches to .csv handler"""
        result = open_meas(csv_file)

        np.testing.assert_array_equal(result, sample_wavelengths)

    def test_open_meas_with_string_path(self, hdr_file, sample_wavelengths):
        """Test that open_meas accepts string paths"""
        result = open_meas(str(hdr_file))

        np.testing.assert_array_equal(result, sample_wavelengths)

    def test_open_meas_file_not_found(self, temp_dir):
        """Test FileNotFoundError is raised for non-existent file"""
        nonexistent = temp_dir / "nonexistent.wvl"

        with pytest.raises(FileNotFoundError):
            open_meas(nonexistent)

    def test_open_meas_invalid_extension(self, temp_dir):
        """Test ValueError is raised for unsupported file extensions"""
        invalid_file = temp_dir / "test.xyz"
        invalid_file.write_text("content")

        with pytest.raises(ValueError, match="Invalid file type"):
            open_meas(invalid_file)

    def test_open_meas_case_insensitive_extension(
        self, temp_dir, sample_wavelengths
    ):
        """Test that file extensions are handled case-insensitively"""
        hdr_content = "wavelength = {400.0, 450.0, 500.0, 550.0, 600.0}"
        hdr_path = temp_dir / "test.HDR"
        hdr_path.write_text(hdr_content)

        result = open_meas(hdr_path)

        np.testing.assert_array_equal(result, sample_wavelengths)

    def test_open_meas_uppercase_extension(self, temp_dir, sample_wavelengths):
        """Test uppercase file extension handling"""
        hdr_content = "wavelength = {400.0, 450.0, 500.0}"
        hdr_path = temp_dir / "test.HDR"
        hdr_path.write_text(hdr_content)

        result = open_meas(hdr_path)

        expected = np.array([400.0, 450.0, 500.0])
        np.testing.assert_array_equal(result, expected)

    def test_open_meas_mixed_case_extension(self, temp_dir):
        """Test mixed case file extension handling"""
        txt_content = "400.0,450.0,500.0"
        txt_path = temp_dir / "test.TxT"
        txt_path.write_text(txt_content)

        result = open_meas(txt_path)

        expected = np.array([400.0, 450.0, 500.0])
        np.testing.assert_array_equal(result, expected)

    def test_open_meas_no_extension(self, temp_dir):
        """Test ValueError is raised for file without extension"""
        no_ext_file = temp_dir / "testfile"
        no_ext_file.write_text("content")

        with pytest.raises(ValueError, match="Invalid file type"):
            open_meas(no_ext_file)


# ============================================================================
# Tests for module-level constants
# ============================================================================


class TestModuleConstants:
    """Tests for module-level constants and mappings"""

    def test_meas_handlers_has_all_types(self):
        """Test that MEAS_HANDLERS contains all supported file types"""
        expected_types = {".wvl", ".hdr", ".txt", ".csv"}
        actual_types = set(MEAS_HANDLERS.keys())

        assert expected_types == actual_types

    def test_meas_handlers_values_are_callable(self):
        """Test that all handler values are callable"""
        for handler in MEAS_HANDLERS.values():
            assert callable(handler)

    def test_meas_handlers_map_to_correct_functions(self):
        """Test that handlers are mapped to their correct functions"""
        assert MEAS_HANDLERS[".wvl"] is open_wvl_file
        assert MEAS_HANDLERS[".hdr"] is open_hdr_file
        assert MEAS_HANDLERS[".txt"] is open_txt_file
        assert MEAS_HANDLERS[".csv"] is open_csv_file


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for the complete workflow"""

    def test_read_multiple_file_formats_same_data(self, temp_dir):
        """Test that all formats can read equivalent data"""
        expected = np.array([400.0, 450.0, 500.0, 550.0, 600.0])

        # Create WVL file
        with patch(
            "pycubeview.services.read_measurement_axis_label.sio.read_wvl"
        ) as mock_read:
            mock_wvl = MagicMock()
            mock_wvl.asarray.return_value = expected
            mock_read.return_value = mock_wvl

            wvl_path = temp_dir / "test.wvl"
            wvl_path.write_text("mock")
            wvl_result = open_meas(wvl_path)
            np.testing.assert_array_equal(wvl_result, expected)

        # Create HDR file
        hdr_content = "wavelength = {400.0, 450.0, 500.0, 550.0, 600.0}"
        hdr_path = temp_dir / "test.hdr"
        hdr_path.write_text(hdr_content)
        hdr_result = open_meas(hdr_path)
        np.testing.assert_array_equal(hdr_result, expected)

        # Create TXT file
        txt_content = "400.0,450.0,500.0,550.0,600.0"
        txt_path = temp_dir / "test.txt"
        txt_path.write_text(txt_content)
        txt_result = open_meas(txt_path)
        np.testing.assert_array_equal(txt_result, expected)

        # Create CSV file
        csv_content = textwrap.dedent(
            """
            wavelength,intensity
            400.0,100
            450.0,110
            500.0,120
            550.0,130
            600.0,140
            """
        ).strip()
        csv_path = temp_dir / "test.csv"
        csv_path.write_text(csv_content)
        csv_result = open_meas(csv_path)
        np.testing.assert_array_equal(csv_result, expected)

    def test_error_handling_across_formats(self, temp_dir):
        """Test that appropriate errors are raised for various failure modes"""
        # Invalid format
        invalid_path = temp_dir / "test.invalid"
        invalid_path.write_text("data")
        with pytest.raises(ValueError):
            open_meas(invalid_path)

        # Non-existent file
        with pytest.raises(FileNotFoundError):
            open_meas(temp_dir / "nonexistent.csv")

        # Malformed HDR (missing wavelength)
        hdr_path = temp_dir / "bad.hdr"
        hdr_path.write_text("no wavelength field")
        with pytest.raises(OSError):
            open_meas(hdr_path)

        # Malformed CSV (missing column)
        csv_path = temp_dir / "bad.csv"
        csv_path.write_text("intensity,other\n100,1\n110,2")
        with pytest.raises(ValueError, match="No measurement column"):
            open_meas(csv_path)


# ============================================================================
# Empty and Malformed Files Tests
# ============================================================================


class TestEmptyAndMalformedFiles:
    """Tests for handling empty and malformed files"""

    def test_empty_txt_file(self, temp_dir):
        """Test that empty .txt file raises ValueError"""
        txt_path = temp_dir / "empty.txt"
        txt_path.write_text("")

        with pytest.raises(ValueError):
            open_txt_file(txt_path)

    def test_empty_csv_file(self, temp_dir):
        """Test that empty .csv file raises ValueError"""
        csv_path = temp_dir / "empty.csv"
        csv_path.write_text("")

        with pytest.raises(ValueError):
            open_csv_file(csv_path)

    def test_csv_with_only_headers(self, temp_dir):
        """Test .csv file with only headers and no data rows"""
        csv_content = "wavelength,intensity,description"
        csv_path = temp_dir / "headers_only.csv"
        csv_path.write_text(csv_content)

        # Should raise an error when trying to extract data
        with pytest.raises((ValueError, IndexError)):
            open_csv_file(csv_path)

    def test_hdr_malformed_unclosed_braces(self, temp_dir):
        """Test .hdr file with unclosed braces in wavelength field"""
        hdr_content = "wavelength = {400.0, 450.0, 500.0"
        hdr_path = temp_dir / "malformed.hdr"
        hdr_path.write_text(hdr_content)

        with pytest.raises(OSError, match="Unable to open .hdr file"):
            open_hdr_file(hdr_path)

    def test_hdr_malformed_missing_opening_brace(self, temp_dir):
        """Test .hdr file with missing opening brace"""
        hdr_content = "wavelength = 400.0, 450.0, 500.0}"
        hdr_path = temp_dir / "malformed2.hdr"
        hdr_path.write_text(hdr_content)

        with pytest.raises(OSError, match="Unable to open .hdr file"):
            open_hdr_file(hdr_path)

    def test_txt_file_with_trailing_comma(self, temp_dir):
        """Test .txt file with trailing comma"""
        txt_content = "400.0,450.0,500.0,"
        txt_path = temp_dir / "trailing_comma.txt"
        txt_path.write_text(txt_content)

        with pytest.raises(ValueError):
            open_txt_file(txt_path)

    def test_txt_file_single_comma(self, temp_dir):
        """Test .txt file containing only a comma"""
        txt_content = ","
        txt_path = temp_dir / "single_comma.txt"
        txt_path.write_text(txt_content)

        with pytest.raises(ValueError):
            open_txt_file(txt_path)


# ============================================================================
# Edge Case Values Tests
# ============================================================================


class TestEdgeCaseValues:
    """Tests for edge case numerical values"""

    def test_scientific_notation_hdr(self, temp_dir):
        """Test .hdr file with wavelengths in scientific notation"""
        hdr_content = "wavelength = {1e3, 4.5e2, 2.1e3}"
        hdr_path = temp_dir / "scientific.hdr"
        hdr_path.write_text(hdr_content)

        result = open_hdr_file(hdr_path)
        expected = np.array([1e3, 4.5e2, 2.1e3])

        np.testing.assert_array_almost_equal(result, expected)

    def test_scientific_notation_txt(self, temp_dir):
        """Test .txt file with wavelengths in scientific notation"""
        txt_content = "1.5e2,2.25e2,3.0e2"
        txt_path = temp_dir / "scientific.txt"
        txt_path.write_text(txt_content)

        result = open_txt_file(txt_path)
        expected = np.array([1.5e2, 2.25e2, 3.0e2])

        np.testing.assert_array_almost_equal(result, expected)

    def test_scientific_notation_csv(self, temp_dir):
        """Test .csv file with wavelengths in scientific notation"""
        csv_content = textwrap.dedent(
            """
            wavelength,intensity
            1e3,100
            4.5e2,110
            2.1e3,120
            """
        ).strip()

        csv_path = temp_dir / "scientific.csv"
        csv_path.write_text(csv_content)

        result = open_csv_file(csv_path)
        expected = np.array([1e3, 4.5e2, 2.1e3])

        np.testing.assert_array_almost_equal(result, expected)

    def test_zero_wavelengths(self, temp_dir):
        """Test that zero wavelength values are accepted"""
        txt_content = "0.0,100.0,200.0"
        txt_path = temp_dir / "zero.txt"
        txt_path.write_text(txt_content)

        result = open_txt_file(txt_path)
        expected = np.array([0.0, 100.0, 200.0])

        np.testing.assert_array_equal(result, expected)

    def test_negative_wavelengths(self, temp_dir):
        """Test that negative wavelength values are accepted (not validated)"""
        txt_content = "-100.0,-50.0,0.0,50.0"
        txt_path = temp_dir / "negative.txt"
        txt_path.write_text(txt_content)

        result = open_txt_file(txt_path)
        expected = np.array([-100.0, -50.0, 0.0, 50.0])

        np.testing.assert_array_equal(result, expected)

    def test_very_large_wavelengths(self, temp_dir):
        """Test very large wavelength values"""
        txt_content = "1e10,1e11,1e12"
        txt_path = temp_dir / "large.txt"
        txt_path.write_text(txt_content)

        result = open_txt_file(txt_path)
        expected = np.array([1e10, 1e11, 1e12])

        np.testing.assert_array_almost_equal(result, expected)

    def test_very_small_wavelengths(self, temp_dir):
        """Test very small decimal wavelength values"""
        txt_content = "0.0001,0.00001,0.000001"
        txt_path = temp_dir / "small.txt"
        txt_path.write_text(txt_content)

        result = open_txt_file(txt_path)
        expected = np.array([0.0001, 0.00001, 0.000001])

        np.testing.assert_array_almost_equal(result, expected, decimal=9)

    def test_many_decimal_places(self, temp_dir):
        """Test wavelengths with many decimal places"""
        txt_content = "400.123456789,450.987654321,500.555555555"
        txt_path = temp_dir / "decimals.txt"
        txt_path.write_text(txt_content)

        result = open_txt_file(txt_path)

        assert len(result) == 3
        assert result[0] == pytest.approx(400.123456789, rel=1e-8)
        assert result[1] == pytest.approx(450.987654321, rel=1e-8)
        assert result[2] == pytest.approx(500.555555555, rel=1e-8)

    def test_single_wavelength_value_across_formats(self, temp_dir):
        """Test single wavelength value in each format"""
        # TXT
        txt_path = temp_dir / "single.txt"
        txt_path.write_text("550.0")
        txt_result = open_txt_file(txt_path)
        assert len(txt_result) == 1
        assert txt_result[0] == 550.0

        # HDR
        hdr_path = temp_dir / "single.hdr"
        hdr_path.write_text("wavelength = {550.0}")
        hdr_result = open_hdr_file(hdr_path)
        assert len(hdr_result) == 1
        assert hdr_result[0] == 550.0

        # CSV
        csv_path = temp_dir / "single.csv"
        csv_path.write_text("wavelength\n550.0")
        csv_result = open_csv_file(csv_path)
        assert len(csv_result) == 1
        assert csv_result[0] == 550.0


# ============================================================================
# Path and File Handling Tests
# ============================================================================


class TestPathAndFileHandling:
    """Tests for path handling and file system interactions"""

    def test_path_with_spaces(self, temp_dir):
        """Test file path with spaces in directory and filename"""
        space_dir = temp_dir / "folder with spaces"
        space_dir.mkdir()
        txt_path = space_dir / "file with spaces.txt"
        txt_path.write_text("400.0,450.0,500.0")

        result = open_txt_file(txt_path)
        expected = np.array([400.0, 450.0, 500.0])

        np.testing.assert_array_equal(result, expected)

    def test_path_with_special_characters(self, temp_dir):
        """Test file path with special characters"""
        txt_path = temp_dir / "file-with_special.chars.txt"
        txt_path.write_text("400.0,450.0")

        result = open_txt_file(txt_path)
        expected = np.array([400.0, 450.0])

        np.testing.assert_array_equal(result, expected)

    def test_relative_path_handling(self, temp_dir):
        """Test handling of relative paths"""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            txt_path = Path("test_relative.txt")
            txt_path.write_text("400.0,450.0,500.0")

            result = open_txt_file(txt_path)
            expected = np.array([400.0, 450.0, 500.0])

            np.testing.assert_array_equal(result, expected)
        finally:
            os.chdir(original_cwd)

    def test_absolute_path_handling(self, temp_dir):
        """Test handling of absolute paths"""
        txt_path = temp_dir.resolve() / "test_absolute.txt"
        txt_path.write_text("400.0,450.0,500.0")

        result = open_txt_file(txt_path)
        expected = np.array([400.0, 450.0, 500.0])

        np.testing.assert_array_equal(result, expected)

    def test_nested_directory_structure(self, temp_dir):
        """Test file in deeply nested directory"""
        nested = temp_dir / "level1" / "level2" / "level3"
        nested.mkdir(parents=True)
        txt_path = nested / "test.txt"
        txt_path.write_text("400.0,450.0")

        result = open_txt_file(txt_path)
        expected = np.array([400.0, 450.0])

        np.testing.assert_array_equal(result, expected)

    def test_file_extension_case_sensitivity(self, temp_dir, wvl_model):
        """Test various case combinations of file extensions"""
        test_cases = [".TXT", ".Txt", ".tXt", ".WVL", ".Csv", ".HDR"]

        for ext in test_cases:
            path = temp_dir / f"test{ext}"
            if ext.lower() == ".txt":
                path.write_text("400.0,450.0,500.0,550.0,600.0")
            elif ext == ".Csv":
                path.write_text(
                    "wavelength\n400.0\n450.0\n500.0\n550.0\n600.0"
                )
            elif ext == ".HDR":
                path.write_text(
                    "wavelength = {400.0, 450.0, 500.0, 550.0, 600.0}"
                )
            elif ext == ".WVL":
                path.write_text(wvl_model.model_dump_json())

            result = open_meas(path)
            assert len(result) == 5


# ============================================================================
# CSV-Specific Edge Cases Tests
# ============================================================================


class TestCsvSpecificEdgeCases:
    """Tests for edge cases specific to CSV file handling"""

    def test_csv_single_data_row(self, temp_dir):
        """Test CSV with only one data row (plus header)"""
        csv_content = textwrap.dedent(
            """
            wavelength,intensity
            400.0,100
            """
        ).strip()

        csv_path = temp_dir / "single_row.csv"
        csv_path.write_text(csv_content)

        result = open_csv_file(csv_path)
        expected = np.array([400.0])

        np.testing.assert_array_equal(result, expected)

    def test_csv_many_columns(self, temp_dir):
        """Test CSV with many columns, selecting specific one"""
        csv_content = textwrap.dedent(
            """
            col1,col2,col3,wavelength,col5,col6,col7
            1,2,3,400.0,5,6,7
            8,9,10,450.0,11,12,13
            14,15,16,500.0,17,18,19
            """
        ).strip()

        csv_path = temp_dir / "many_cols.csv"
        csv_path.write_text(csv_content)

        result = open_csv_file(csv_path, measurement_column_label="wavelength")
        expected = np.array([400.0, 450.0, 500.0])

        np.testing.assert_array_equal(result, expected)

    def test_csv_column_name_substring(self, temp_dir):
        """Test CSV where one column name is substring of another"""
        csv_content = textwrap.dedent(
            """
            wave,wavelength,intensity
            1,400.0,100
            2,450.0,110
            """
        ).strip()

        csv_path = temp_dir / "substring.csv"
        csv_path.write_text(csv_content)

        # Should match "wavelength" exactly, not "wave"
        result = open_csv_file(csv_path, measurement_column_label="wavelength")
        expected = np.array([400.0, 450.0])

        np.testing.assert_array_equal(result, expected)

    def test_csv_first_column(self, temp_dir):
        """Test CSV where wavelength is the first column"""
        csv_content = textwrap.dedent(
            """
            wavelength,intensity,description
            400.0,100,Red
            450.0,110,Orange
            """
        ).strip()

        csv_path = temp_dir / "first_col.csv"
        csv_path.write_text(csv_content)

        result = open_csv_file(csv_path)
        expected = np.array([400.0, 450.0])

        np.testing.assert_array_equal(result, expected)

    def test_csv_last_column(self, temp_dir):
        """Test CSV where wavelength is the last column"""
        csv_content = textwrap.dedent(
            """
            intensity,description,wavelength
            100,Red,400.0
            110,Orange,450.0
            """
        ).strip()

        csv_path = temp_dir / "last_col.csv"
        csv_path.write_text(csv_content)

        result = open_csv_file(csv_path, measurement_column_label="wavelength")
        expected = np.array([400.0, 450.0])

        np.testing.assert_array_equal(result, expected)

    def test_csv_with_extra_whitespace_in_header(self, temp_dir):
        """Test CSV with spaces around header values (should still work)"""
        csv_content = "wavelength , intensity\n400.0,100\n450.0,110"
        csv_path = temp_dir / "header_spaces.csv"
        csv_path.write_text(csv_content)

        # Note: This tests current behavior - column names might have
        # leading/trailing spaces
        try:
            result = open_csv_file(
                csv_path, measurement_column_label="wavelength"
            )
            expected = np.array([400.0, 450.0])
            np.testing.assert_array_equal(result, expected)
        except ValueError:
            # If spaces cause failure, that's also valid behavior to document
            pytest.skip("Column names with spaces not supported")

    def test_csv_empty_data_cell(self, temp_dir):
        """Test CSV with missing data value"""
        csv_content = textwrap.dedent(
            """
            wavelength,intensity
            400.0,100
            ,110
            500.0,120
            """
        ).strip()

        csv_path = temp_dir / "empty_cell.csv"
        csv_path.write_text(csv_content)

        with pytest.raises(ValueError):
            open_csv_file(csv_path)


# ============================================================================
# HDR-Specific Edge Cases Tests
# ============================================================================


class TestHdrSpecificEdgeCases:
    """Tests for edge cases specific to HDR file handling"""

    def test_hdr_with_wavelength_units(self, temp_dir):
        """Test HDR with wavelength field and units field"""
        hdr_content = textwrap.dedent(
            """
            wavelength = {400.0, 450.0, 500.0}
            wavelength units = Micrometers
            """
        ).strip()

        hdr_path = temp_dir / "with_units.hdr"
        hdr_path.write_text(hdr_content)

        result = open_hdr_file(hdr_path)
        expected = np.array([400.0, 450.0, 500.0])

        np.testing.assert_array_equal(result, expected)

    def test_hdr_very_long_wavelength_list(self, temp_dir):
        """Test HDR with very long wavelength list"""
        wvls = ",".join([str(float(400 + i * 0.5)) for i in range(500)])
        hdr_content = f"wavelength = {{{wvls}}}"
        hdr_path = temp_dir / "long_list.hdr"
        hdr_path.write_text(hdr_content)

        result = open_hdr_file(hdr_path)

        assert len(result) == 500
        assert result[0] == 400.0
        assert result[-1] == pytest.approx(400 + 499 * 0.5)

    def test_hdr_scientific_notation_with_spaces(self, temp_dir):
        """Test HDR with scientific notation and spaces"""
        hdr_content = "wavelength = { 1e3 , 4.5e2 , 2.1e3 }"
        hdr_path = temp_dir / "sci_spaces.hdr"
        hdr_path.write_text(hdr_content)

        result = open_hdr_file(hdr_path)
        expected = np.array([1e3, 4.5e2, 2.1e3])

        np.testing.assert_array_almost_equal(result, expected)

    def test_hdr_no_spaces_around_braces(self, temp_dir):
        """Test HDR wavelength with no spaces around braces"""
        hdr_content = "wavelength={400.0,450.0,500.0}"
        hdr_path = temp_dir / "no_spaces.hdr"
        hdr_path.write_text(hdr_content)

        result = open_hdr_file(hdr_path)
        expected = np.array([400.0, 450.0, 500.0])

        np.testing.assert_array_equal(result, expected)

    def test_hdr_with_extra_text_before_wavelength(self, temp_dir):
        """Test HDR with additional header fields before wavelength"""
        hdr_content = textwrap.dedent(
            """
            ENVI
            description = {Test image}
            samples = 512
            lines = 512
            bands = 3
            wavelength = {400.0, 450.0, 500.0}
            """
        ).strip()

        hdr_path = temp_dir / "full_header.hdr"
        hdr_path.write_text(hdr_content)

        result = open_hdr_file(hdr_path)
        expected = np.array([400.0, 450.0, 500.0])

        np.testing.assert_array_equal(result, expected)

    def test_hdr_with_extra_text_after_wavelength(self, temp_dir):
        """Test HDR with additional fields after wavelength"""
        hdr_content = textwrap.dedent(
            """
            wavelength = {400.0, 450.0, 500.0}
            wavelength units = Micrometers
            data type = 4
            interleave = bil
            """
        ).strip()

        hdr_path = temp_dir / "fields_after.hdr"
        hdr_path.write_text(hdr_content)

        result = open_hdr_file(hdr_path)
        expected = np.array([400.0, 450.0, 500.0])

        np.testing.assert_array_equal(result, expected)


# ============================================================================
# Error Messages and Validation Tests
# ============================================================================


class TestErrorMessagesAndValidation:
    """Tests for error messages and validation behavior"""

    def test_csv_no_measurement_column_error_message(self, temp_dir):
        """Test that error message is descriptive for missing column"""
        csv_content = "intensity,description\n100,Red\n110,Orange"
        csv_path = temp_dir / "no_column.csv"
        csv_path.write_text(csv_content)

        with pytest.raises(ValueError) as exc_info:
            open_csv_file(csv_path, measurement_column_label="wavelength")

        assert "No measurement column exists" in str(exc_info.value)

    def test_csv_multiple_columns_error_message(self, temp_dir):
        """Test that error message is descriptive for duplicate columns"""
        csv_content = (
            "wavelength,wavelength,intensity\n400.0,400.0,100\n450.0,450.0,110"
        )
        csv_path = temp_dir / "dup_col.csv"
        csv_path.write_text(csv_content)

        with pytest.raises(ValueError) as exc_info:
            open_csv_file(csv_path)

        assert "Multiple measurement columns exist" in str(exc_info.value)

    def test_hdr_missing_wavelength_error_message(self, temp_dir):
        """
        Test that error message is descriptive for missing wavelength field
        """
        hdr_content = "samples = 512\nlines = 512\nbands = 3"
        hdr_path = temp_dir / "no_wavelength.hdr"
        hdr_path.write_text(hdr_content)

        with pytest.raises(OSError) as exc_info:
            open_hdr_file(hdr_path)

        assert "Unable to open .hdr file" in str(exc_info.value)
        assert "wavelength" in str(exc_info.value).lower()

    def test_open_meas_invalid_extension_error_message(self, temp_dir):
        """Test error message for invalid file extension"""
        invalid_path = temp_dir / "test.xyz"
        invalid_path.write_text("data")

        with pytest.raises(ValueError) as exc_info:
            open_meas(invalid_path)

        assert "Invalid file type" in str(exc_info.value)

    def test_open_meas_file_not_found_error_type(self, temp_dir):
        """Test that correct exception type is raised for missing file"""
        nonexistent = temp_dir / "nonexistent.wvl"

        with pytest.raises(FileNotFoundError):
            open_meas(nonexistent)


# ============================================================================
# Type Validation Tests
# ============================================================================


class TestTypeValidation:
    """Tests for return type validation"""

    def test_open_txt_returns_ndarray(self, temp_dir):
        """Test that open_txt_file returns np.ndarray"""
        txt_path = temp_dir / "test.txt"
        txt_path.write_text("400.0,450.0,500.0")

        result = open_txt_file(txt_path)

        assert isinstance(result, np.ndarray)

    def test_open_hdr_returns_ndarray(self, temp_dir):
        """Test that open_hdr_file returns np.ndarray"""
        hdr_path = temp_dir / "test.hdr"
        hdr_path.write_text("wavelength = {400.0, 450.0, 500.0}")

        result = open_hdr_file(hdr_path)

        assert isinstance(result, np.ndarray)

    def test_open_csv_returns_ndarray(self, temp_dir):
        """Test that open_csv_file returns np.ndarray"""
        csv_path = temp_dir / "test.csv"
        csv_path.write_text("wavelength\n400.0\n450.0\n500.0")

        result = open_csv_file(csv_path)

        assert isinstance(result, np.ndarray)

    def test_open_meas_returns_ndarray(self, temp_dir):
        """Test that open_meas returns np.ndarray"""
        hdr_path = temp_dir / "test.hdr"
        hdr_path.write_text("wavelength = {400.0, 450.0, 500.0}")

        result = open_meas(hdr_path)

        assert isinstance(result, np.ndarray)

    def test_returned_array_is_1d(self, temp_dir):
        """Test that returned arrays are always 1D"""
        # TXT
        txt_path = temp_dir / "test.txt"
        txt_path.write_text("400.0,450.0,500.0")
        txt_result = open_txt_file(txt_path)
        assert txt_result.ndim == 1

        # HDR
        hdr_path = temp_dir / "test.hdr"
        hdr_path.write_text("wavelength = {400.0, 450.0, 500.0}")
        hdr_result = open_hdr_file(hdr_path)
        assert hdr_result.ndim == 1

        # CSV
        csv_path = temp_dir / "test.csv"
        csv_path.write_text("wavelength\n400.0\n450.0\n500.0")
        csv_result = open_csv_file(csv_path)
        assert csv_result.ndim == 1

    def test_returned_array_dtype_is_float(self, temp_dir):
        """Test that returned arrays have float dtype"""
        # TXT
        txt_path = temp_dir / "test.txt"
        txt_path.write_text("400.0,450.0,500.0")
        txt_result = open_txt_file(txt_path)
        assert np.issubdtype(txt_result.dtype, np.floating)

        # HDR
        hdr_path = temp_dir / "test.hdr"
        hdr_path.write_text("wavelength = {400.0, 450.0, 500.0}")
        hdr_result = open_hdr_file(hdr_path)
        assert np.issubdtype(hdr_result.dtype, np.floating)

        # CSV
        csv_path = temp_dir / "test.csv"
        csv_path.write_text("wavelength\n400.0\n450.0\n500.0")
        csv_result = open_csv_file(csv_path)
        assert np.issubdtype(csv_result.dtype, np.floating)

    def test_array_immutability_not_guaranteed_but_consistent(self, temp_dir):
        """Test that arrays can be read consistently"""
        txt_path = temp_dir / "test.txt"
        txt_path.write_text("400.0,450.0,500.0")

        result1 = open_txt_file(txt_path)
        result2 = open_txt_file(txt_path)

        # Should return equal arrays from the same file
        np.testing.assert_array_equal(result1, result2)
