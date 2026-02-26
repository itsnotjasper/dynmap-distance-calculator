import sys
import json
import argparse
import re
from urllib.request import Request, urlopen
import datetime
from pathlib import Path
from typing import Any, Optional, Literal, get_args
# constants
url = "https://dynmap.minecartrapidtransit.net/main/tiles/_markers_/marker_new.json"
output = ".\\json\\"+str(int(datetime.datetime.now(datetime.UTC).timestamp()))+"_markers.json"

def fetchJson(url, output):
    headers = {"Accept": "application/json, */*;q=0.1"}
    request = Request(url, headers=headers)
    try:
        response = urlopen(request)
    except:
        response = urlopen(url, context=ssl._create_unverified_context())
    data = json.loads(response.read().decode("utf-8"))
    return data

def updateJson(fetchMRT:bool, force=False, verbose=True):
    # default
    bypass = False
    latestEpoch = int(datetime.datetime.now(datetime.UTC).timestamp())
    if not Path('./json/').exists():
        Path('./json/').mkdir(parents=True, exist_ok=True)
        bypass=True
        force=True
        if verbose:
            print(f"./json/ does not exist, directory created and fetching new data")
    elif not any(Path("./json").glob("*_markers.json")):
        bypass=True
        force=True
        if verbose:
            print(f"No existing JSON files found in ./json/, fetching new data")

    if not bypass or not force:
        latestJson = max(Path("./json").glob("*_markers.json"), key=lambda p: int(p.stem.split("_")[0]))
        latestEpoch = int(latestJson.stem.split("_")[0])
        if verbose:
            print(f"Latest JSON: {latestJson}")
            print(f"Latest Epoch: {latestEpoch}")

    if latestEpoch+86400 < int(datetime.datetime.now(datetime.UTC).timestamp()) or force:
        print("Fetching new JSON data")
        if not fetchMRT:
            data = fetchJson(url, output).get("sets", {})
            aRoads = data.get("roads.a", {})
            bRoads = data.get("roads.b", {})
            data = {"roads.a": aRoads, "roads.b": bRoads}
        elif fetchMRT:
            data = fetchJson(url, output).get("sets", {})
        with open(output, "w") as f:
            json.dump(data, f, indent=2)
        if verbose:
            print(output + " created")
        return output
    else:
        print("Using cached JSON data, use --fetch to force update")
        return ".\\"+str(latestJson)

if __name__ == "__main__":
    updateJson(True, force=True)