import math
import numbers

from os import path
from datetime import timedelta


def extract_water_level_grid(run_path, grid_size, base_date_time, run_date_time, out_dir):
    TIMEDEP_OUT_PATH = path.join(run_path, 'output', 'TIMDEP.OUT')
    CADPTS_DAT_PATH = path.join(run_path, 'output', 'CADPTS.DAT')
    WATER_LEVEL_DEPTH_MIN = 0.3
    buffer_size = 65536
    with open(TIMEDEP_OUT_PATH) as infile:
        waterLevelLines = []
        boundary = _get_grid_boudary(CADPTS_DAT_PATH)
        # print("boundary : ", boundary)
        CellGrid = _get_cell_grid(CADPTS_DAT_PATH, boundary, gap=grid_size)
        # print("CellGrid : ", CellGrid)
        while True:
            lines = infile.readlines(buffer_size)
            if not lines:
                break
            for line in lines:
                if len(line.split()) == 1:
                    if len(waterLevelLines) > 0:
                        waterLevels = _get_water_level_grid(waterLevelLines)
                        EsriGrid = _get_esri_grid(waterLevels, boundary, CellGrid, WATER_LEVEL_DEPTH_MIN, gap=grid_size)

                        # Get Time stamp Ref:http://stackoverflow.com/a/13685221/1461060
                        ModelTime = float(waterLevelLines[0].split()[0])
                        fileModelTime = base_date_time
                        fileModelTime = fileModelTime + timedelta(hours=ModelTime)
                        dateAndTime = fileModelTime.strftime("%Y-%m-%d_%H-%M-%S")
                        if fileModelTime >= run_date_time:
                            # Create files
                            fileName = "%s-%s.%s" % ('water_level_grid', dateAndTime, 'asc')
                            file_path = path.join(out_dir, fileName)
                            with open(file_path, 'w') as F:
                                F.writelines(EsriGrid)
                            print('Prepared: ', fileName)
                        else:
                            print('Skip. Current model time:' + dateAndTime +
                                  ' is not greater than ' + run_date_time.strftime("%Y-%m-%d_%H-%M-%S"))
                        waterLevelLines = []
                waterLevelLines.append(line)
        return True


def _get_water_level_grid(lines):
    waterLevels = []
    for line in lines[1:]:
        if line == '\n':
            break
        v = line.split()
        # Get flood level (Elevation)
        # waterLevels.append('%s %s' % (v[0], v[1]))
        # Get flood depth (Depth)
        waterLevels.append('%s %s' % (v[0], v[1]))
    return waterLevels


def _get_esri_grid(waterLevels, boudary, CellMap, water_level_depth_min,  gap=250.0, missingVal=-9):
    "Esri GRID format : https://en.wikipedia.org/wiki/Esri_grid"
    "ncols         4"
    "nrows         6"
    "xllcorner     0.0"
    "yllcorner     0.0"
    "cellsize      50.0"
    "NODATA_value  -9999"
    "-9999 -9999 5 2"
    "-9999 20 100 36"
    "3 8 35 10"
    "32 42 50 6"
    "88 75 27 9"
    "13 5 1 -9999"

    EsriGrid = []

    cols = int(math.ceil((boudary['long_max'] - boudary['long_min']) / gap)) + 1
    rows = int(math.ceil((boudary['lat_max'] - boudary['lat_min']) / gap)) + 1
    # print('>>>>>  cols: %d, rows: %d' % (cols, rows))

    Grid = [[missingVal for x in range(cols)] for y in range(rows)]

    for level in waterLevels:
        v = level.split()
        i, j = CellMap[int(v[0])]
        if i >= cols or j >= rows:
            pass
            # TODO log these things
            # print('i: %d, j: %d, cols: %d, rows: %d' % (i, j, cols, rows))
            # print(boudary)
        if float(v[1]) >= water_level_depth_min:
            Grid[j][i] = float(v[1])

    EsriGrid.append('%s\t%s\n' % ('ncols', cols))
    EsriGrid.append('%s\t%s\n' % ('nrows', rows))
    EsriGrid.append('%s\t%s\n' % ('xllcorner', boudary['long_min'] - 125))
    EsriGrid.append('%s\t%s\n' % ('yllcorner', boudary['lat_min'] - 125))
    EsriGrid.append('%s\t%s\n' % ('cellsize', gap))
    EsriGrid.append('%s\t%s\n' % ('NODATA_value', missingVal))

    for j in range(0, rows):
        arr = []
        for i in range(0, cols):
            arr.append(Grid[j][i])

        EsriGrid.append('%s\n' % (' '.join(str(x) for x in arr)))
    return EsriGrid


def _get_grid_boudary(cad_pts_file_path):
    "longitude  -> x : larger value"
    "latitude   -> y : smaller value"

    long_min = 1000000000.0
    lat_min = 1000000000.0
    long_max = 0.0
    lat_max = 0.0

    with open(cad_pts_file_path) as f:
        lines = f.readlines()
        for line in lines :
            values = line.split()
            long_min = min(long_min, float(values[1]))
            lat_min = min(lat_min, float(values[2]))

            long_max = max(long_max, float(values[1]))
            lat_max = max(lat_max, float(values[2]))

    return {
        'long_min': long_min,
        'lat_min': lat_min,
        'long_max': long_max,
        'lat_max': lat_max
    }


def _get_cell_grid(cad_pts_file_path, boudary, gap=250.0):
    CellMap = {}

    cols = int(math.ceil((boudary['long_max'] - boudary['long_min']) / gap)) + 1
    rows = int(math.ceil((boudary['lat_max'] - boudary['lat_min']) / gap)) + 1

    with open(cad_pts_file_path) as f:
        lines = f.readlines()
        for line in lines :
            v = line.split()
            i = int((float(v[1]) - boudary['long_min']) / gap)
            j = int((float(v[2]) - boudary['lat_min']) / gap)
            if not isinstance(i, numbers.Integral) or not isinstance(j, numbers.Integral):
                pass
                # TODO log this
                # print('### WARNING i: %d, j: %d, cols: %d, rows: %d' % (i, j, cols, rows))
            if i >= cols or j >= rows:
                pass
                # TODO log this
                # print('### WARNING i: %d, j: %d, cols: %d, rows: %d' % (i, j, cols, rows))
            if i >= 0 or j >= 0 :
                CellMap[int(v[0])] = (i, rows - j -1)

    return CellMap
