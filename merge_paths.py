import math
from typing import List, Tuple
def dist(p1, p2):
    return math.hypot(p1[0]-p2[0], p1[1]-p2[1], p1[2]-p2[2])
def merge_paths(segments: List[Tuple[List[float], List[float], List[float]]], verbose=False):
    if not segments:
        return [], [], []
    print("Processing segments...")
    segment_data = []
    for x, y, z in segments:
        x = list(x)
        y = list(y)
        z = list(z)
        first = (x[0], y[0], z[0])
        last = (x[-1], y[-1], z[-1])
        segment_data.append({
            'x': x,
            'y': y,
            'z': z,
            'first': first,
            'last': last,
            'used': False
        })

    current = segment_data[0]
    current['used'] = True
    combined = list(zip(current['x'], current['y'], current['z']))
    first_pt = combined[0]
    last_pt = combined[-1]
    remaining = [i for i in range(1, len(segment_data))]
    while remaining:
        best_dist = float('inf')
        best_i = None
        best_attach_to_front = None
        best_reverse = None

        for i in remaining:
            seg = segment_data[i]
            # Distances to our current ends
            d_first_to_first = dist(seg['first'], first_pt)
            d_first_to_last  = dist(seg['first'], last_pt)
            d_last_to_first  = dist(seg['last'], first_pt)
            d_last_to_last   = dist(seg['last'], last_pt)

            if d_last_to_first < best_dist:
                best_dist = d_last_to_first
                best_i = i
                best_attach_to_front = True
                best_reverse = False

            if d_first_to_first < best_dist:
                best_dist = d_first_to_first
                best_i = i
                best_attach_to_front = True
                best_reverse = True


            if d_first_to_last < best_dist:
                best_dist = d_first_to_last
                best_i = i
                best_attach_to_front = False
                best_reverse = False

            if d_last_to_last < best_dist:
                best_dist = d_last_to_last
                best_i = i
                best_attach_to_front = False
                best_reverse = True

        seg = segment_data[best_i]
        seg_pts = list(zip(seg['x'], seg['y'], seg['z']))
        if best_reverse:
            seg_pts.reverse()

        if best_attach_to_front:
            combined = seg_pts + combined
            first_pt = combined[0]
        else:
            combined = combined + seg_pts
            last_pt = combined[-1]

        seg['used'] = True
        remaining.remove(best_i)
    x_out, y_out, z_out = zip(*combined) if combined else ([], [], [])
    return list(x_out), list(y_out), list(z_out)

