from os import path
from datetime import timedelta

from .general import get_run_date_times


def extract_channel_water_levels(run_path, channel_cell_map):
    HYCHAN_OUT_PATH = path.join(run_path, 'output', 'HYCHAN.OUT')
    base_dt, run_dt = get_run_date_times(run_path)

    channel_tms_length = _get_timeseries_length(HYCHAN_OUT_PATH)
    channel_tms = _get_channel_timeseries(HYCHAN_OUT_PATH, 'water-level', channel_tms_length, base_dt, channel_cell_map)

    return _change_keys(channel_cell_map, channel_tms)


def extract_flood_plane_water_levels(run_path, flood_plane_map):
    TIMDEP_OUT_PATH = path.join(run_path, 'output', 'TIMDEP.OUT')
    base_dt, run_dt = get_run_date_times(run_path)

    flood_plane_tms = _get_flood_plain_timeseries(TIMDEP_OUT_PATH, base_dt, flood_plane_map)

    return _change_keys(flood_plane_map, flood_plane_tms)


def extract_water_discharge(run_path, channel_cell_map):
    HYCHAN_OUT_PATH = path.join(run_path, 'output', 'HYCHAN.OUT')
    channel_tms_length = _get_timeseries_length(HYCHAN_OUT_PATH)
    base_dt, run_dt = get_run_date_times(run_path)

    channel_tms = _get_channel_timeseries(HYCHAN_OUT_PATH, 'discharge', channel_tms_length, base_dt, channel_cell_map)

    return _change_keys(channel_cell_map, channel_tms)


def _get_timeseries_length(hychan_file_path):
    # Calculate the size of time series
    bufsize = 65536
    series_length = 0
    with open(hychan_file_path) as infile:
        is_water_level_lines = False
        is_counting = False
        count_series_size = 0  # HACK: When it comes to the end of file, unable to detect end of time series
        while True:
            lines = infile.readlines(bufsize)
            if not lines or series_length:
                break
            for line in lines:
                if line.startswith('CHANNEL HYDROGRAPH FOR ELEMENT NO:', 5):
                    is_water_level_lines = True
                elif is_water_level_lines:
                    cols = line.split()
                    if len(cols) > 0 and cols[0].replace('.', '', 1).isdigit():
                        count_series_size += 1
                        is_counting = True
                    elif is_water_level_lines and is_counting:
                        series_length = count_series_size
                        break
    return series_length


def _get_channel_timeseries(hychan_file_path, output_type, series_length, base_time, cell_map):

    hychan_out_mapping = {
        'water-level': 1,
        'water-depth': 2,
        'discharge': 4
    }

    # Extract Channel Water Level elevations from HYCHAN.OUT file
    ELEMENT_NUMBERS = cell_map.keys()
    MISSING_VALUE = -999
    bufsize = 65536
    waterLevelSeriesDict = dict.fromkeys(ELEMENT_NUMBERS, [])
    with open(hychan_file_path) as infile:
        is_water_level_lines = False
        is_series_complete = False
        waterLevelLines = []
        seriesSize = 0  # HACK: When it comes to the end of file, unable to detect end of time series
        while True:
            lines = infile.readlines(bufsize)
            if not lines:
                break
            for line in lines:
                if line.startswith('CHANNEL HYDROGRAPH FOR ELEMENT NO:', 5):
                    seriesSize = 0
                    elementNo = line.split()[5]

                    if elementNo in ELEMENT_NUMBERS:
                        is_water_level_lines = True
                        waterLevelLines.append(line)
                    else:
                        is_water_level_lines = False

                elif is_water_level_lines:
                    cols = line.split()
                    if len(cols) > 0 and isfloat(cols[0]):
                        seriesSize += 1
                        waterLevelLines.append(line)

                        if seriesSize == series_length:
                            is_series_complete = True

                if is_series_complete:
                    timeseries = []
                    elementNo = waterLevelLines[0].split()[5]
                    print('Extracted Cell No', elementNo, cell_map[elementNo])
                    for ts in waterLevelLines[1:]:
                        v = ts.split()
                        if len(v) < 1:
                            continue
                        # Get flood level (Elevation)
                        value = v[hychan_out_mapping[output_type]]
                        # Get flood depth (Depth)
                        # value = v[2]
                        if not isfloat(value):
                            value = MISSING_VALUE
                            continue  # If value is not present, skip
                        if value == 'NaN':
                            continue  # If value is NaN, skip
                        timeStep = float(v[0])
                        currentStepTime = base_time + timedelta(hours=timeStep)
                        dateAndTime = currentStepTime.strftime("%Y-%m-%d %H:%M:%S")
                        timeseries.append([dateAndTime, value])
                    waterLevelSeriesDict[elementNo] = timeseries
                    is_water_level_lines = False
                    is_series_complete = False
                    waterLevelLines = []
        return waterLevelSeriesDict


def _get_flood_plain_timeseries(timdep_file_path, base_time, cell_map):
    # Extract Flood Plain water elevations from BASE.OUT file
    bufsize = 65536
    MISSING_VALUE = -999
    ELEMENT_NUMBERS = cell_map.keys()
    with open(timdep_file_path) as infile:
        waterLevelLines = []
        waterLevelSeriesDict = dict.fromkeys(ELEMENT_NUMBERS, [])
        while True:
            lines = infile.readlines(bufsize)
            if not lines:
                break
            for line in lines:
                if len(line.split()) == 1:
                    if len(waterLevelLines) > 0:
                        waterLevels = _get_water_level_of_channels(waterLevelLines, ELEMENT_NUMBERS)
                        # Get Time stamp Ref:http://stackoverflow.com/a/13685221/1461060
                        ModelTime = float(waterLevelLines[0].split()[0])
                        currentStepTime = base_time + timedelta(hours=ModelTime)
                        dateAndTime = currentStepTime.strftime("%Y-%m-%d %H:%M:%S")

                        for elementNo in ELEMENT_NUMBERS:
                            tmpTS = waterLevelSeriesDict[elementNo][:]
                            if elementNo in waterLevels:
                                tmpTS.append([dateAndTime, waterLevels[elementNo]])
                            else:
                                tmpTS.append([dateAndTime, MISSING_VALUE])
                            waterLevelSeriesDict[elementNo] = tmpTS
                        waterLevelLines = []
                waterLevelLines.append(line)
        return waterLevelSeriesDict


def _change_keys(key_map, dict_to_be_mapped):
    dict_ = {}
    for key in key_map.keys():
        dict_[key_map[key]] = dict_to_be_mapped[key]
    return dict_


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def _get_water_level_of_channels(lines, channels=None):
    """
     Get Water Levels of given set of channels
    :param lines:
    :param channels:
    :return:
    """
    if channels is None:
        channels = []
    water_levels = {}
    for line in lines[1:]:
        if line == '\n':
            break
        v = line.split()
        if v[0] in channels:
            # Get flood level (Elevation)
            water_levels[v[0]] = v[5]
            # Get flood depth (Depth)
            # water_levels[int(v[0])] = v[2]
    return water_levels
