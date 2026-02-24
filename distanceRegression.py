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


    def distCalc(self, start, end):
        proj_start = self.project_point(start)
        proj_end = self.project_point(end)

        dist_start = proj_start['pathDist']
        dist_end = proj_end['pathDist']


        if dist_start < dist_end:
            return {
                'dist': dist_end - dist_start,
                'direction': 1,
                'startProjection': proj_start,
                'endProjection': proj_end,
                'conf': proj_start['conf'] * proj_end['conf']
            }
        else:
            return {
                'dist': dist_start - dist_end,
                'direction': -1,
                'startProjection': proj_end,
                'endProjection': proj_start,
                'conf': proj_start['conf'] * proj_end['conf']
            }



if __name__ == '__main__':
    x = [0,1,2,3,4,5,6,7]
    y = [0,2,4,6,8,10,12,14]
    z = [0,4,8,12,16,20,24,28]
    
    path = PathTraverse(x, y, z, vertical=True)

    project = path.distCalc((0.5, 1.2, 2.2), (6.6, 13, 25))
    print(f"Distance is {project['dist']:.3f}, confidence is {project['conf']:.3f}")
                    

        















# '''
# Linear Regression. Determines the distance from the user-given points to any two points given by markers, provides an uncertainty and confidence interval estimation.
# Inputs: List of x-coordinates, y-coordinates, z-coordinates, starting user-given point, ending user-given point.

# Outputs: Between which two points this point fits in the best, their indices, confidence estimation (0 to 1)
# '''
# def PointRegression(x: list, y: list, z: list, position: tuple, verbose=False, vertical=False):
#     # Constants
#     pointOnMarker = False
#     uncertainty = 0
#     confidence = 1
#     # First, to check whether these points lie on any markers:
#     for i in range(len(x)):
#         if Pythagorean(position, (x[i], y[i], z[i]), vertical) < 3:
#             uncertainty = 3
#             indexPosition = i
#             if verbose:
#                 print(f"Point at ({position[0]}, {position[1]}, {position[2]}) is very close to marker at ({x[i]}, {y[i]}, {z[i]}).")
#             return (indexPosition, uncertainty, confidence)
#     # For the pain.
#     segment_length = []
#     for j in range(len(x) - 1):
#         segment_length.append(Pythagorean((x[j],y[j],z[j]),(x[j+1],y[j+1],z[j+1])), vertical)
#         if verbose:
#             print(f"Segment length of index {j} added to list")
#     sigma = 0.5*sum(segment_length)/len(x)
#     segment_distance = []
#     uncertainties = []
#     # Let Vector A be x,y,z[j], Vector B be x,y,z[j+1] and the Vector P be the position tuple.
#     if vertical:
#         for k in range(len(x) - 1):
#             Ax, Az = x[k], z[k]
#             Bx, Bz = x[k+1], z[k+1]
#             Px, Pz = position[0], position[2]

#             ABx = Bx - Ax
#             ABz = Bz - Az

#             APx = Px - Ax
#             APz = Pz - Az

#             d_AB = ABx**2 + ABz**2
#             # degenerate segment AB
#             if d_AB == 0:
#                 delta = math.hypot(APx, APz)
#                 print("Degenerate segment found")
#             else:
#                 t = (APx*ABx + APz*ABz) / d_AB
#                 t = max(0.00, min(1.00, t))
#                 Cx = Ax + t*ABx
#                 Cz = Az + t*ABz
#                 delta = math.hypot(Px - Cx, Pz - Cz)
#                 uncert = (Px - Cx + Pz - Cz) - delta
#                 print(f"Minimum distance for index {k} found")
#             segment_distance.append(delta)
#             uncertainties.append(uncert)
#             if verbose:
#                 print(f"Segment distance of {delta} at index {k} added")
#                 print(f"Uncertainty of {uncert} at index {k} added")
#     else:
#         for k in range(len(x) - 1):
#             Ax, Ay, Az = x[k], y[k], z[k]
#             Bx, By, Bz = x[k+1], y[k+1], z[k+1]
#             Px, Py, Pz = position[0], position[1], position[2]

#             ABx = Bx - Ax
#             ABy = By - Ay
#             ABz = Bz - Az

#             APx = Px - Ax
#             APy = Py - Ay
#             APz = Pz - Az

#             d_AB = ABx**2 + ABy**2 + ABz**2
#             # degenerate segment AB
#             if d_AB == 0:
#                 delta = math.hypot(APx, APy, APz)
#                 print("Degenerate segment found")
#             else:
#                 t = (APx*ABx + APy*ABy + APz*ABz) / d_AB
#                 t = max(0.00, min(1.00, t))
#                 Cx = Ax + t*ABx
#                 Cy = Ay + t*ABy
#                 Cz = Az + t*ABz
#                 delta = math.hypot(Px - Cx, Py - Cy, Pz - Cz)
#                 uncert = (Px - Cx + Py - Cy + Pz - Cz) - delta
#                 print(f"Minimum distance for index {k} found")
#             segment_distance.append(delta)
#             uncertainties.append(uncert)
#             if verbose:
#                 print(f"Segment distance of {delta} at index {k} added")
#                 print(f"Uncertainty of {uncert} at index {k} added")
#     minIndex = min(range(len(segment_distance)))
#     distMin = segment_distance[minIndex]
#     uncertainty = uncertainties[minIndex]
#     confidence = math.exp(-(distMin/sigma)**2)



#     return (indexPosition, uncertainty, confidence)

# def pathDirection(x: list, y: list, z:list, start: tuple, end: tuple, verbose=False, vertical=False):
#     '''
#     Returns -1 if path is backward
#     Returns 0 if points are on the same segment
#     Returns 1 if path is forward
#     '''
#     ind_start, uncert_start, conf_start = PointRegression(x, y, z, start, verbose, vertical)
#     ind_end, uncert_end, conf_end = PointRegression(x, y, z, end, verbose, vertical)
#     traversal = None
#     path_indices = []
#     totalConfidence = 1
#     if ind_start == ind_end:
#         traversal = 0
#     elif ind_end > ind_start:
#         traversal = 1
#         path_indices = list(range(ind_start, ind_end+2))
#     elif ind_end < ind_start:
#         traversal = -1
#         path_indices = list(range(ind_start, ind_end-1, -1))
    
#     totalConfidence = conf_start * conf_end
    


    
