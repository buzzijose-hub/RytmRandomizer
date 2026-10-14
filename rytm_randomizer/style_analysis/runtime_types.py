"""Shared runtime narrowing for process and serialization boundaries."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


class AudioFileInfo(Protocol):
    frames: int
    samplerate: int
    channels: int
    subtype: str


class LibrosaOnsetApi(Protocol):
    onset_strength: Callable[..., NDArray[np.float64]]
    onset_detect: Callable[..., NDArray[np.int64]]


class LibrosaFeatureApi(Protocol):
    spectral_centroid: Callable[..., NDArray[np.float64]]
    spectral_flatness: Callable[..., NDArray[np.float64]]
    rms: Callable[..., NDArray[np.float64]]
    zero_crossing_rate: Callable[..., NDArray[np.float64]]


class LibrosaApi(Protocol):
    onset: LibrosaOnsetApi
    feature: LibrosaFeatureApi
    get_duration: Callable[..., float]
    load: Callable[..., tuple[NDArray[np.float64], int]]
    stft: Callable[..., NDArray[np.complex128]]
    fft_frequencies: Callable[..., NDArray[np.float64]]
    pyin: Callable[..., tuple[NDArray[np.float64], NDArray[np.bool_], NDArray[np.float64]]]
    resample: Callable[..., NDArray[np.float64]]


_RuntimeValue = TypeVar("_RuntimeValue")


def require_runtime_type(
    value: object,
    expected_type: type[_RuntimeValue],
    message: str,
) -> _RuntimeValue:
    """Return ``value`` narrowed to ``expected_type`` or fail closed."""

    if not isinstance(value, expected_type):
        raise TypeError(message)
    return value


__all__ = ["AudioFileInfo", "LibrosaApi", "require_runtime_type"]
