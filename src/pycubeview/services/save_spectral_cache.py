# Built-Ins
from pathlib import Path
import shutil

# Local Imports
from pycubeview.data_transfer_classes import Measurement
from pycubeview.custom_types import SaveMode

# Dependencies
import spectralio as sio
import numpy as np


def save_spectral_cache(
    measurements: list[Measurement],
    save_dir: Path,
    wavelength_model: sio.WvlModel,
    geodata_fp: Path | None,
    group_name: str,
    cube_data: np.ndarray,
    save_mode: SaveMode,
) -> None:
    """
    Saves the measurement cache, assuming it represents spectral data.

    Parameters
    ----------
    measurements : list[Measurement]
        A list of Measurement objects to be saved.
    save_dir : Path
        The directory where the measurements will be saved.
    wavelength_model : sio.WvlModel
        The wavelength model to be used for the spectral data.
    group_name : str
        The name of the measurement session, used for naming files.
    cube_data : np.ndarray
        Cube data in a numpy array format.
    """
    # Setting up save bins
    point_saves: list[sio.PointSpectrum1D] = []
    group_saves: list[sio.SpectrumGroup] = []

    # Saving .spec and .specgrp files.
    for meas in measurements:
        save_path = Path(save_dir, meas.name)
        if meas.type == "Point":
            _save_point_spectrum(
                meas, save_path, wavelength_model, point_saves
            )
        elif meas.type == "Group":
            _save_group_spectrum(
                meas, save_path, wavelength_model, cube_data, group_saves
            )

    # Saving shapefiles, if geodata is set.
    if geodata_fp is not None:
        _save_geodata_shapefiles(
            point_saves,
            group_saves,
            save_dir,
            group_name,
            geodata_fp,
            save_mode,
        )


def _save_point_spectrum(
    measurement: Measurement,
    save_path: Path,
    wavelength_model: sio.WvlModel,
    point_saves: list[sio.PointSpectrum1D],
) -> None:
    """Save a single point spectrum to disk."""
    _spec = sio.Spectrum1D(
        name=measurement.name,
        spectrum=list(measurement.yvalues),
        wavelength=wavelength_model,
        bbl_applied=True,
    )
    spec = sio.PointSpectrum1D.from_pixel_coord(
        x=measurement.pixel_x, y=measurement.pixel_y, spec1d=_spec
    )
    sio.write_from_object(spec, save_path)
    point_saves.append(spec)


def _save_group_spectrum(
    measurement: Measurement,
    save_path: Path,
    wavelength_model: sio.WvlModel,
    cube_data: np.ndarray,
    group_saves: list[sio.SpectrumGroup],
) -> None:
    """Save a group of point spectra to disk."""
    if (measurement.x_pixels is None) or (measurement.y_pixels is None):
        return

    spec_list: list[sio.PointSpectrum1D] = []
    spec_points: list[tuple[int, int]] = []
    for n in range(measurement.x_pixels.size):
        x = measurement.x_pixels[n]
        y = measurement.y_pixels[n]
        _spec = sio.Spectrum1D(
            name=measurement.name,
            spectrum=list(cube_data[y, x, :]),
            wavelength=wavelength_model,
            bbl_applied=True,
        )
        spec = sio.PointSpectrum1D.from_pixel_coord(x=x, y=y, spec1d=_spec)
        spec_list.append(spec)
        spec_points.append((x, y))

    spec_grp = sio.SpectrumGroup(
        name=measurement.name,
        spectra=spec_list,
        spectra_pts=spec_points,
        wavelength=wavelength_model,
    )
    sio.write_from_object(spec_grp, save_path)
    group_saves.append(spec_grp)


def _save_geodata_shapefiles(
    point_saves: list[sio.PointSpectrum1D],
    group_saves: list[sio.SpectrumGroup],
    save_dir: Path,
    group_name: str,
    geodata_fp: Path,
    save_mode: SaveMode,
) -> None:
    """Save shapefiles for point and group measurements using geodata."""
    geoloc = sio.read_geodata(geodata_fp)
    shp_file_dir = Path(save_dir, f"{group_name}.shapes")
    if (save_mode == "Group") and not shp_file_dir.exists():
        shp_file_dir.mkdir()

    if save_mode == "Individual":
        with open(
            Path(save_dir, f"{group_name}_spectra").with_suffix(".txt"), "w"
        ) as f:
            f.write(f"Group Name: {group_name}\n\n\n")

    if len(point_saves) > 0:
        _save_point_shapefiles(
            point_saves, shp_file_dir, save_dir, group_name, geoloc, save_mode
        )

    if len(group_saves) > 0:
        _save_group_shapefiles(
            group_saves,
            shp_file_dir,
            save_dir,
            group_name,
            geodata_fp,
            save_mode,
        )


def _save_point_shapefiles(
    point_saves: list[sio.PointSpectrum1D],
    shp_file_dir: Path,
    save_dir: Path,
    group_name: str,
    geoloc: sio.BaseGeolocationModel,
    save_mode: SaveMode,
) -> None:
    """Save point shapefiles based on save mode."""
    geo_point_saves = [
        sio.GeoSpectrum1D.from_point_spec(geoloc, i) for i in point_saves
    ]

    if save_mode == "Group":
        sio.make_points(
            geo_point_saves,
            Path(shp_file_dir, f"{group_name}_points").with_suffix(".shp"),
        )
    elif save_mode == "Individual":
        with open(
            Path(save_dir, f"{group_name}_spectra").with_suffix(".txt"), "a"
        ) as f:
            f.write("----Point Spectra----\n")
            for i in geo_point_saves:
                spectrum_dir = Path(save_dir, i.name)
                spectrum_dir.mkdir(exist_ok=True)
                _spec_file = Path(save_dir, i.name).with_suffix(".pntspec")
                sio.make_points(
                    [i], Path(spectrum_dir, f"{i.name}").with_suffix(".shp")
                )
                shutil.move(_spec_file, Path(spectrum_dir, _spec_file.name))
                f.write(f"{i.name}\n")
            f.write("\n")


def _save_group_shapefiles(
    group_saves: list[sio.SpectrumGroup],
    shp_file_dir: Path,
    save_dir: Path,
    group_name: str,
    geodata_fp: Path,
    save_mode: SaveMode,
) -> None:
    """Save group shapefiles based on save mode."""
    if save_mode == "Group":
        sio.make_polygons(
            group_saves,
            geodata_fp,
            Path(shp_file_dir, f"{group_name}_areas").with_suffix(".shp"),
        )
    elif save_mode == "Individual":
        with open(
            Path(save_dir, f"{group_name}_spectra").with_suffix(".txt"), "a"
        ) as f:
            f.write("----Area Spectra----\n")
            for j in group_saves:
                spectrum_dir = Path(save_dir, j.name)
                spectrum_dir.mkdir(exist_ok=True)
                _spec_file = Path(save_dir, j.name).with_suffix(".specgrp")
                sio.make_polygons(
                    [j],
                    geodata_fp,
                    Path(spectrum_dir, f"{j.name}").with_suffix(".shp"),
                )
                shutil.move(_spec_file, Path(spectrum_dir, _spec_file.name))
                f.write(f"{j.name}\n")
