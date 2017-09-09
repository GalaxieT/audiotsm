# -*- coding: utf-8 -*-

"""
audiotsm.wsola
~~~~~~~~~~~~~

This module implements the WSOLA (Waveform Similarity-based Overlap-Add)
time-scale modification procedure.

WSOLA works in the same way as OLA, with the exception that it allows slight
shift of the position of the analysis frames.
"""

import numpy as np

from audiotsm.base import AnalysisSynthesisTSM, Converter
from audiotsm.utils.windows import hanning


class WSOLAConverter(Converter):
    """A Converter implementing the WSOLA (Waveform Similarity-based
    Overlap-Add) time-scale modification procedure."""
    def __init__(self, channels, frame_length, synthesis_hop, tolerance):
        self._channels = channels
        self._frame_length = frame_length
        self._synthesis_hop = synthesis_hop
        self._tolerance = tolerance

        self._synthesis_frame = np.empty((channels, frame_length))
        self._natural_progression = np.empty((channels, frame_length))
        self._first = True

    def clear(self):
        self._first = True

    def convert_frame(self, analysis_frame):
        for k in range(0, self._channels):
            if self._first:
                delta = 0
            else:
                cross_correlation = np.correlate(
                    analysis_frame[k, :-self._synthesis_hop],
                    self._natural_progression[k])
                delta = np.argmax(cross_correlation)
                del cross_correlation

            # Copy the shifted analysis frame to the synthesis frame buffer
            np.copyto(self._synthesis_frame[k],
                      analysis_frame[k, delta:delta + self._frame_length])

            # Save the natural progression (what the next synthesis frame would
            # be at normal speed)
            delta += self._synthesis_hop
            np.copyto(self._natural_progression[k],
                      analysis_frame[k, delta:delta + self._frame_length])

        self._first = False

        return self._synthesis_frame


def wsola(channels=2, speed=1., frame_length=1024, analysis_hop=None,
          synthesis_hop=None, tolerance=None):
    """Returns a TSM object implementing the WSOLA (Waveform Similarity-based
    Overlap-Add) time-scale modification procedure.

    :param channels: (optional) the number of channels of the audio signal.
    :type channels: int
    :param speed: (optional) the speed ratio by which the speed of the signal
        will be multiplied (for example, 0.5 means the output will be half as
        fast as the input). It will be ignored if the analysis_hop argument is
        set.
    :type speed: float
    :param frame_length: (optional) the length of the frames.
    :type frame_length: int
    :param speed: (optional) the speed ratio by which the speed of the signal
        will be multiplied (for example, 0.5 means the output will be half as
        fast as the input). It will be ignored if the analysis_hop argument is
        set.
    :type speed: float
    :param analysis_hop: (optional) the number of samples between two
        consecutive analysis frames (``speed * synthesis_hop`` by default)
    :type analysis_hop: int
    :param synthesis_hop: (optional) the number of samples between two
        consecutive synthesis frames (half the frame_length by default)
    :type synthesis_hop: int
    :param tolerance: the maximum number of samples that the analysis frame can
        be shifted.
    :type tolerance: int
    :returns: a :class:`base.TSM` object
    """
    # pylint: disable=too-many-arguments
    if synthesis_hop is None:
        synthesis_hop = frame_length // 2

    if analysis_hop is None:
        analysis_hop = int(synthesis_hop * speed)

    if tolerance is None:
        tolerance = frame_length // 2

    analysis_window = None
    synthesis_window = hanning(frame_length)

    converter = WSOLAConverter(channels, frame_length, synthesis_hop,
                               tolerance)

    return AnalysisSynthesisTSM(
        converter, channels, frame_length, analysis_hop, synthesis_hop,
        analysis_window, synthesis_window, tolerance,
        tolerance + synthesis_hop)
