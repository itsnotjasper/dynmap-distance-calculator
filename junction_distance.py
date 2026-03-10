import sys
import os
import json
import argparse
import re 
import curses
from urllib.request import Request, urlopen
import datetime
from pathlib import Path
from typing import Any, Optional
import time

from json_changes import fetchJson, updateJson
from distanceRegression import PathTraverse
from merge_paths import merge_paths

lineDict = {"A": "Arctic", "B": "Beach", "C": "Circle", "D": "Desert", "E": "Eastern", "F": "Forest", 
"G": "Garden", "H": "Savannah", "I": "Island", "J": "Jungle", "K": "Knight", "L": "Lakeshore", 
"M": "Mesa", "N": "Northern", "O": "Oasis", "P": "Plains", "Q": "", "R": "Rose", "S": "Southern", "T": "Taiga",
"U": "Union", "V": "Valley", "W": "Western", "X": "Expo", "Y": "Yeti", "Z": "Zephyr"}

def getOptions(search, data, MRTQuery:bool, MRTline=None):
    if not MRTQuery:
        options = []
        for i in data['roads.a']['lines']:
            options.append(i)
        for j in data['roads.b']['lines']:
            options.append(j)
        matches = [match for match in options if search.lower() in match.lower()]
        return sorted(matches) if matches else [f"No matches for {search}"]
    else:
        options = []
        # print(data[lineDict[MRTline].lower()]['lines'])
        for i in data[lineDict[MRTline].lower()]['lines']:
            options.append(i)
        return sorted(options)


def selector(stdscr, options, data):
    curses.curs_set(0)  
    stdscr.keypad(True) 
        
        # Initialize color if supported
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
        
    current_row = 0
    selected = [False] * len(options)
        
    if options and options[0].startswith("No matches for"):
        selectable = False
    else:
        selectable = True

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx() 
            # Title
        title = "↑/↓, Space to toggle, Enter to confirm, q to quit)"
        if len(title) > width - 1:
            title = title[:width-1]
        stdscr.addstr(0, 0, title)
            
        try:
            stdscr.addstr(1, 0, "-" * (width - 1))
        except curses.error:
            pass
            
        for i in range(len(options)):
            checkbox = "[x]" if selected[i] else "[ ]"
            try:
                label = data['roads.a']['lines'][options[i]]['label']
            except:
                label = data['roads.b']['lines'][options[i]]['label']
            line = f"{checkbox} {options[i]} (Name: {label})"
            if i == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(i + 2, 0, line)
                stdscr.attroff(curses.color_pair(1))
            else:

                stdscr.attron(curses.A_NORMAL)
                stdscr.addstr(i + 2, 0, line)
            
        status = f"Selected: {sum(selected)}/{len(options)}"
        stdscr.addstr(height-1, 0, status[:width-1])
            
        stdscr.refresh()
            
            # Handle key input
        key = stdscr.getch()
            
        if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(options) - 1:
                current_row += 1
        elif key == ord(' ') and selectable:
                selected[current_row] = not selected[current_row]
        elif key == ord('\n') or key == ord('\r'):
            if selectable:
                return [i for i, s in enumerate(selected) if s]
            else:
                return []  # No selectable items
        elif key == ord('q'):
            return None


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ident", help="Road Number / 'MRT' for MRT lines")
    parser.add_argument("-f", "--fetch", "--force", action="store_true", help="Force fetch new JSON data")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-y", "--vertical", action="store_true", help="Takes into consideration y-axis")
    parser.add_argument("-n", "--interval", type=float, default=None, metavar="N",
                        help="Print (x, y, z) coordinates every N blocks along the path")
    args = parser.parse_args(argv)
    if args.ident.upper() != "MRT":  
        newJson = updateJson(False, force=args.fetch, verbose=args.verbose)
        with open(newJson, 'r') as f:
            data = json.load(f)

        options = getOptions(args.ident, data, False)
        if not options:
            print(f"No options for search {args.ident}")
            return
        
        selectedI = curses.wrapper(selector, options, data)
        if selectedI is None:
            print("Selection cancelled")
        elif selectedI:
            markerList = []
            for i in selectedI:
                if args.verbose:
                    print(f"{options[i]} indexing")
                try:
                    markerList.append((data['roads.a']['lines'][options[i]]['x'], data['roads.a']['lines'][options[i]]['y'], data['roads.a']['lines'][options[i]]['z']))
                    # print(data['roads.a']['lines'][options[i]]['x'])
                    # print(markerList)
                except:
                    markerList.append((data['roads.b']['lines'][options[i]]['x'], data['roads.b']['lines'][options[i]]['y'], data['roads.b']['lines'][options[i]]['z']))
                    # print(data['roads.b']['lines'][options[i]]['x'])
                    # print(markerList)
            merged_x, merged_y, merged_z = merge_paths(markerList, args.verbose)
            path = PathTraverse(merged_x, merged_y, merged_z, args.verbose, args.vertical)
            valid = False
            while not valid:
                print("Do you want to use custom junctions (start/end)? (Y/N) \n")
                ans = input("").upper()
                if ans == "Y" or ans == "N":
                    valid = True
                else:
                    print("Invalid response")
                    time.sleep(0.3)

            if ans == "Y":
                valid = False
                while not valid:
                    print(f"Please enter coordinates of measured start in the format (x, y, z), or leave blank to start at first marker at ({merged_x[0]}, {merged_y[0]}, {merged_z[0]}). \n")
                    start = input("").strip()
                    if start == "":
                        valid = True
                    else:
                        parts = start.replace(',', ' ').split()
                        if len(parts) != 3:
                            print("Invalid coordinates")
                            time.sleep(0.3)
                            continue
                        try:
                            xStart, yStart, zStart = map(float, parts)
                            valid = True
                        except:
                            print("Invalid coordinates")
                            time.sleep(0.3)
                if start == "":
                    xStart = merged_x[0]
                    yStart = merged_y[0]
                    zStart = merged_z[0]
                valid = False
                while not valid:
                    print(f"Please enter coordinates of measured end in the format (x, y, z), or leave blank to end at last marker at ({merged_x[-1]}, {merged_y[-1]}, {merged_z[-1]}). \n")
                    end = input("").strip()
                    if end == "":
                        valid = True
                    else:
                        parts2 = end.replace(',', ' ').split()
                        if len(parts2) != 3:
                            print("Invalid coordinates")
                            time.sleep(0.3)
                            continue
                        try:
                            xEnd, yEnd, zEnd = map(float, parts2)
                            valid = True
                        except:
                            print("Invalid coordinates")
                            time.sleep(0.3)
                if end == "":
                    xEnd = merged_x[-1]
                    yEnd = merged_y[-1]
                    zEnd = merged_z[-1]
            if ans == "N":
                xStart = merged_x[0]
                yStart = merged_y[0]
                zStart = merged_z[0]
                xEnd = merged_x[-1]
                yEnd = merged_y[-1]
                zEnd = merged_z[-1]
            pathInfo = path.distCalc((xStart, yStart, zStart), (xEnd, yEnd, zEnd))
            if pathInfo.get('circular'):
                print(f"Circular road detected — two possible paths (confidence {pathInfo['conf']:.3f}):")
                print(f"  Clockwise distance:     {pathInfo['clockwise']['dist']:.3f}")
                print(f"  Anticlockwise distance: {pathInfo['anticlockwise']['dist']:.3f}")
            else:
                print(f"Estimated distance is: {pathInfo['dist']:.3f}, with confidence {pathInfo['conf']:.3f}.")
            if args.verbose:
                print(f"""Starting projection:
                Best Segment: {pathInfo['startProjection']['seg']},
                Projection Error: {pathInfo['startProjection']['projErr']},
                Confidence: {pathInfo['startProjection']['conf']:.3f}
                """)
                print(f"""Ending projection:
                Best Segment: {pathInfo['endProjection']['seg']},
                Projection Error: {pathInfo['endProjection']['projErr']},
                Confidence: {pathInfo['endProjection']['conf']:.3f}
                """)
            if args.interval is not None:
                start_dist = pathInfo['startProjection']['pathDist']
                end_dist   = pathInfo['endProjection']['pathDist']
                if pathInfo.get('circular'):
                    total    = path.cum_distances[-1]
                    forward  = abs(end_dist - start_dist)
                    backward = total - forward
                    if forward <= backward:
                        wps = path.waypoints(start_dist, end_dist, args.interval)
                    else:
                        # Walk the long way around the loop
                        adj_end = end_dist + total if end_dist < start_dist else end_dist - total
                        wps = path.waypoints(start_dist, adj_end, args.interval)
                else:
                    wps = path.waypoints(start_dist, end_dist, args.interval)
                header = f"Waypoints every {args.interval} blocks ({len(wps)} point{'s' if len(wps) != 1 else ''}):"
                out_lines = [header]
                for idx, (wx, wy, wz) in enumerate(wps):
                    if idx == 0:
                        label = "start"
                    elif idx == len(wps) - 1:
                        label = "end"
                    else:
                        label = f"{idx * args.interval:.1f}"
                    out_lines.append(f"  [{label:>8}]  x={wx:>10.3f},  y={wy:>8.3f},  z={wz:>10.3f}")
                output_text = "\n".join(out_lines)
                print(f"\n{output_text}")
                Path("./outputs").mkdir(parents=True, exist_ok=True)
                epoch = int(datetime.datetime.now(datetime.UTC).timestamp())
                out_path = f"./outputs/{args.ident}_{epoch}.txt"
                with open(out_path, "w") as f:
                    f.write(output_text + "\n")
                print(f"Waypoints saved to {out_path}")
        else:
            print("No items selected")
    elif args.ident.upper() == "MRT":
        newJson = updateJson(True, force=args.fetch, verbose=args.verbose)
        with open(newJson, 'r') as f:
            data = json.load(f)
        valid = False
        while not valid:
            userLine = input("Enter the alphabet representing the line, for example Z for Zephyr: \n").upper()
            try:
                line = data[lineDict[userLine].lower()]
                valid = True
            except:
                print("Invalid line.")
                time.sleep(0.3)
        markerLabels = getOptions("", data, True, userLine)
        markerList = []
        for i in range(len(markerLabels)):
            markerList.append((line['lines'][markerLabels[i]]['x'], line['lines'][markerLabels[i]]['y'], line['lines'][markerLabels[i]]['z']))
        merged_x, merged_y, merged_z = merge_paths(markerList, args.verbose)
        path = PathTraverse(merged_x, merged_y, merged_z, args.verbose, args.vertical)
        valid = False
        while not valid:
            print("Do you want to use custom measurements (start/end)? (Y/N) \n")
            ans = input("").upper()
            if ans == "Y" or ans == "N":
                valid = True
            else:
                print("Invalid response")
                time.sleep(0.3)

            if ans == "Y":
                valid = False
                while not valid:
                    print(f"Please enter coordinates of measured start in the format (x, y, z), or leave blank to start at first marker at ({merged_x[0]}, {merged_y[0]}, {merged_z[0]}). \n")
                    start = input("").strip()
                    if start == "":
                        valid = True
                    else:
                        parts = start.replace(',', ' ').split()
                        if len(parts) != 3:
                            print("Invalid coordinates")
                            time.sleep(0.3)
                            continue
                        try:
                            xStart, yStart, zStart = map(float, parts)
                            valid = True
                        except:
                            print("Invalid coordinates")
                            time.sleep(0.3)
                if start == "":
                    xStart = merged_x[0]
                    yStart = merged_y[0]
                    zStart = merged_z[0]
                valid = False
                while not valid:
                    print(f"Please enter coordinates of measured end in the format (x, y, z), or leave blank to end at last marker at ({merged_x[-1]}, {merged_y[-1]}, {merged_z[-1]}). \n")
                    end = input("").strip()
                    if end == "":
                        valid = True
                    else:
                        parts2 = end.replace(',', ' ').split()
                        if len(parts2) != 3:
                            print("Invalid coordinates")
                            time.sleep(0.3)
                            continue
                        try:
                            xEnd, yEnd, zEnd = map(float, parts2)
                            valid = True
                        except:
                            print("Invalid coordinates")
                            time.sleep(0.3)
                if end == "":
                    xEnd = merged_x[-1]
                    yEnd = merged_y[-1]
                    zEnd = merged_z[-1]
            if ans == "N":
                xStart = merged_x[0]
                yStart = merged_y[0]
                zStart = merged_z[0]
                xEnd = merged_x[-1]
                yEnd = merged_y[-1]
                zEnd = merged_z[-1]
            pathInfo = path.distCalc((xStart, yStart, zStart), (xEnd, yEnd, zEnd))
            if pathInfo.get('circular'):
                print(f"Circular road detected — two possible paths (confidence {pathInfo['conf']:.3f}):")
                print(f"  Clockwise distance:     {pathInfo['clockwise']['dist']:.3f}")
                print(f"  Anticlockwise distance: {pathInfo['anticlockwise']['dist']:.3f}")
            else:
                print(f"Estimated distance is: {pathInfo['dist']:.3f}, with confidence {pathInfo['conf']:.3f}.")
            if args.verbose:
                print(f"""Starting projection:
                Best Segment: {pathInfo['startProjection']['seg']},
                Projection Error: {pathInfo['startProjection']['projErr']},
                Confidence: {pathInfo['startProjection']['conf']:.3f}
                """)
                print(f"""Ending projection:
                Best Segment: {pathInfo['endProjection']['seg']},
                Projection Error: {pathInfo['endProjection']['projErr']},
                Confidence: {pathInfo['endProjection']['conf']:.3f}
                """)





if __name__ == "__main__":
    sys.exit(main())