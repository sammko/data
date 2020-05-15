import argparse
import json
import os
import sys
from collections import defaultdict, namedtuple
from datetime import date, datetime

import fastjsonschema
import yaml
from fastjsonschema.exceptions import JsonSchemaException


def school_year_from_date(date: date) -> str:
    if date.month < 9:
        return "%d_%d" % (date.year - 1, date.year % 100)
    return "%d_%d" % (date.year, (date.year + 1) % 100)


ErrorData = namedtuple("ErrorData", ["file", "message"])
ERRORS = []
OUTPUT = defaultdict(lambda: [])
ROOT = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument(
    "--dry", action="store_true", help="Only validate, do not build output files."
)
args = parser.parse_args()


with open(os.path.join(ROOT, "schemas", "event.schema.json")) as f:
    validate_event = fastjsonschema.compile(json.load(f))

for directory in os.walk(os.path.join(ROOT, "data")):
    for file in directory[2]:
        name, ext = os.path.splitext(file)
        if ext.lower() not in [".yaml", ".yml"]:
            continue
        path = os.path.join(directory[0], file)

        with open(path) as f:
            event_data = yaml.safe_load(f)
            try:
                validate_event(event_data)
                if not args.dry:
                    event_date = datetime.strptime(
                        event_data["date"]["start"], "%Y-%m-%d"
                    ).date()
                    OUTPUT[school_year_from_date(event_date)].append(event_data)
                print(".", end="", flush=True)
            except JsonSchemaException as e:
                ERRORS.append(ErrorData(path, e.message))
                print("F", end="", flush=True)

print("\n")

if len(ERRORS):
    for error in ERRORS:
        print("Error validating file %s:\n\t%s" % (error.file, error.message))
    sys.exit(1)

if not args.dry:
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    for year, events in OUTPUT.items():
        print("Writing output for year %s." % (year))

        with open(os.path.join(ROOT, "build", "%s.json" % (year)), "w") as f:
            json.dump(events, f)
