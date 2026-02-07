"""
Processing Utilities for individual measurements

Different sets of processing utilities for various applications, including:
    - "spectral_processing"
"""

# Built-Ins
from typing import Optional, TypeVar, Generic, Any
from dataclasses import dataclass

# Dependencies
import reflspeckit as rsk

# Local Imports
from pycubeview.data_transfer_classes import Measurement
from pycubeview.custom_types import SpectralProcessingStepLiteral

T = TypeVar("T")


@dataclass
class ProcessingFlag(Generic[T]):
    step: T
    config: dict[str, Any]


def spectral_processing(
    *,
    measurement: Optional[Measurement] = None,
    spectrum: Optional[rsk.Spec1D] = None,
    processing_flags: list[ProcessingFlag[SpectralProcessingStepLiteral]] = [],
) -> rsk.Spec1D:
    """
    Apply a sequence of spectral processing steps to `spectrum`.
    """
    if (measurement is not None) and (spectrum is None):
        spectrum = rsk.Spec1D(measurement.yvalues, measurement.xvalues)
    elif (spectrum is not None) and (measurement is None):
        pass
    else:
        raise ValueError(
            "Exactly one of spectrum and measurement must be None."
        )

    # Normalize input to a mutable list
    if processing_flags is None:
        processing_flags = []

    # Use structural pattern matching to peel off the head of the sequence
    match processing_flags:
        case []:
            # No more steps
            return spectrum

        case [flag, *rest]:
            match flag.step:
                case "OUTLIER_REMOVAL":
                    spectrum.outlier_removal(**flag.config)
                    return spectral_processing(
                        spectrum=spectrum, processing_flags=rest
                    )
                case "FILTERING":
                    spectrum.noise_reduction(**flag.config)
                    return spectral_processing(
                        spectrum=spectrum, processing_flags=rest
                    )
                case "CONTINUUM_REMOVAL":
                    spectrum.continuum_removal(**flag.config)
                    return spectral_processing(
                        spectrum=spectrum, processing_flags=rest
                    )

        case flags:
            # Fallback for unexpected contents
            raise TypeError(f"Unsupported processing flags: {flags!r}")
