import math
import json
from typing import List, Tuple, Optional

# BEFORE YOU READ THIS: THIS IS HORRIFIC CODE! I AM NOT RESPONSIBLE FOR THE LOSS OF YOUR BRAINCELLS.

class PathTraverse:
    def __init__(self, x, y, z, verbose=False, vertical=False):
        self.x = x
        self.z = z
        self._seg_lengths = None
        self._cum_distances = None
        self.verbose = verbose
        self.vertical = vertical
        # probably find a way to optimise not importing y later
        self.y = y

    @property
    def seg_lengths(self):
        if self._seg_lengths is None:
            self._compute_seg_data()
        
        return self._seg_lengths
    
    @property
    def cum_distances(self):
        if self._cum_distances is None:
            self._compute_seg_data()
        
        return self._cum_distances
    
    def _compute_seg_data(self):
        self._seg_lengths = []
        self._cum_distances = [0.0]
        if self.vertical:
            for i in range(len(self.x) - 1):
                dx = self.x[i+1] - self.x[i]
                dy = self.y[i+1] - self.y[i]
                dz = self.z[i+1] - self.z[i]
                dist = math.hypot(dx, dy, dz)
                self._seg_lengths.append(dist)
                self._cum_distances.append(self._cum_distances[-1] + dist)
        else:
            for i in range(len(self.x) - 1):
                dx = self.x[i+1] - self.x[i]
                dz = self.z[i+1] - self.z[i]
                dist = math.hypot(dx, dz)
                self._seg_lengths.append(dist)
                self._cum_distances.append(self._cum_distances[-1] + dist)
            
    def _get_seg_info(self, i):
        dx = self.x[i+1] - self.x[i]
        dz = self.z[i+1] - self.z[i]
        if self.vertical:
            dy = self.y[i+1] - self.y[i]
        else:
            dy = 0
        return ((self.x[i],self.y[i], self.z[i]), (self.x[i+1], self.y[i+1], self.z[i+1]), (dx, dy, dz))

    def project_point(self, point):
        px, py, pz = point
        best_dist = float('inf')
        best_info = None
        best_segment = 0
        best_t = 0
        best_proj = None

        for i in range(len(self.x) - 1):
            if self.verbose:
                print(f"Now checking segment {i}:")
            (x1, y1, z1), (x2, y2, z2), (dx, dy, dz) = self._get_seg_info(i)
            if self.vertical:
                if (px < min(x1, x2) - best_dist or px > max(x1, x2)+best_dist or pz < min(z1, z2) or pz > max(z1, z2)+best_dist or py < min(y1, y2) or py > max(y1, y2)+best_dist):
                    continue
            else:
                if (px < min(x1, x2) - best_dist or px > max(x1, x2)+best_dist or pz < min(z1, z2) or pz > max(z1, z2)+best_dist):
                    continue
            if self.vertical:
                seg_len = dx**2+dy**2+dz**2
                if seg_len < 1e-12: # degenerate segments
                    proj = (x1, y1, z1)
                    t = 0
                    dist = (px-x1)**2 + (py-y1)**2 + (pz-z1)**2
                else:
                    vx = px - x1
                    vy = py - y1
                    vz = pz - z1
                    t = (vx*dx + vy*dy + vz*dz) / seg_len
                    t = max(0.0, min(1.0,t))
                    projx = x1+t*dx
                    projy = y1+t*dy
                    projz = z1+t*dz
                    proj = (projx, projy, projx)
                    dist = (px-projx)**2+(py-projy)**2+(pz-projz)**2
            else:
                seg_len = dx**2+dz**2
                if seg_len < 1e-12: # degenerate segments
                    proj = (x1, y1, z1)
                    t = 0
                    dist = (px-x1)**2 + (pz-z1)**2
                else:
                    vx = px - x1
                    vz = pz - z1
                    t = (vx*dx + vz*dz) / seg_len
                    t = max(0.0, min(1.0,t))
                    projx = x1+t*dx
                    projz = z1+t*dz
                    proj = (projx, 0, projz)
                    dist = (px-projx)**2+(pz-projz)**2

            if dist < best_dist:
                if self.verbose:
                    print(f"Better segment found: segment {i}")
                best_dist = dist
                best_segment = i
                best_t = t
                best_proj = proj
        
        best_dist = math.sqrt(best_dist)
        print(f"Best distance found.")
        if self.cum_distances is not None:
            path_dist = self.cum_distances[best_segment] + best_t*self._seg_lengths[best_segment]
        
        else:
            path_dist = 0.0
            for i in range(best_segment):
                _, _, (dx, dy, dz) = self._get_seg_info(i)
                if self.vertical:
                    path_dist += best_t*math.hypot(dx, dy, dz)
                else:
                    path_dist += best_t*math.hypot(dx, dz)
            
        if self._seg_lengths is not None:
            seg_length = self.seg_lengths[best_segment]
        else:
            _, _, (dx, dy, dz) = self._get_seg_info(best_segment)
            if self.vertical:
                seg_length = math.hypot(dx, dy, dz)
            else:
                seg_length = math.hypot(dx, dz)
        
        confidence = math.exp( -best_dist / (seg_length + 1e-6))
        res = { 
            'seg': best_segment,
            't': best_t,
            'pathDist': path_dist,
            'projPoint': best_proj,
            'projErr': best_dist,
            'conf': confidence
        }

        return res


    def is_circular(self, threshold=50.0):
        """
        Returns True if the path forms a closed loop, i.e. the first and last
        points are within `threshold` units of each other.
        """
        if len(self.x) < 3:
            return False
        if self.vertical:
            gap = math.hypot(
                self.x[-1] - self.x[0],
                self.y[-1] - self.y[0],
                self.z[-1] - self.z[0]
            )
        else:
            gap = math.hypot(
                self.x[-1] - self.x[0],
                self.z[-1] - self.z[0]
            )
        return gap <= threshold

    def distCalc(self, start, end, circular_threshold=50.0):
        proj_start = self.project_point(start)
        proj_end = self.project_point(end)

        dist_start = proj_start['pathDist']
        dist_end = proj_end['pathDist']
        conf = proj_start['conf'] * proj_end['conf']

        if self.is_circular(circular_threshold):
            total_length = self.cum_distances[-1]
            # Forward path (clockwise): distance along the array from start to end
            forward = abs(dist_end - dist_start)
            # Backward path (anticlockwise): going the other way around the loop
            backward = total_length - forward
            if self.verbose:
                print(f"Circular path detected. Total loop length: {total_length:.3f}")
                print(f"Clockwise: {forward:.3f}, Anticlockwise: {backward:.3f}")
            return {
                'circular': True,
                'clockwise':     {'dist': forward,   'direction':  1},
                'anticlockwise': {'dist': backward,  'direction': -1},
                'startProjection': proj_start,
                'endProjection': proj_end,
                'conf': conf
            }

        # Non-circular: original behaviour
        if dist_start < dist_end:
            return {
                'circular': False,
                'dist': dist_end - dist_start,
                'direction': 1,
                'startProjection': proj_start,
                'endProjection': proj_end,
                'conf': conf
            }
        else:
            return {
                'circular': False,
                'dist': dist_start - dist_end,
                'direction': -1,
                'startProjection': proj_end,
                'endProjection': proj_start,
                'conf': conf
            }