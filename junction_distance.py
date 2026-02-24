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

def getOptions(search, data):
    options = []
    for i in data['roads.a']['lines']:
        options.append(i)
    for j in data['roads.b']['lines']:
        options.append(j)
    matches = [road for road in options if search.lower() in road.lower()]
    return sorted(matches) if matches else [f"No matches for {search}"]

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
    parser.add_argument("road", help="Road Number")
    parser.add_argument("-f", "--fetch", "--force", action="store_true", help="Force fetch new JSON data")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-y", "--vertical", action="store_true", help="Takes into consideration y-axis")
    args = parser.parse_args(argv)
    newJson = updateJson(force=args.fetch, verbose=args.verbose)
    with open(newJson, 'r') as f:
        data = json.load(f)

    options = getOptions(args.road, data)
    if not options:
        print(f"No options for search {args.road}")
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
    else:
        print("No items selected")

if __name__ == "__main__":
    sys.exit(main())