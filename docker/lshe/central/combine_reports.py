#!/usr/bin/env python3
"""
Combine every centre's LSHE report for one month into a single CSV, add
all-centre totals, and list the centres whose report is missing.

    python3 combine_reports.py --month 2027-03 \
        [--collected collected] [--centres centres.conf] [--output-dir combined]

Reads <collected>/<CENTRE_CODE>/lshe_<CENTRE_CODE>_<YYYY-MM>.csv (as written
by collect_reports.sh) and writes:

    combined/lshe_ALL_<YYYY-MM>.csv           every centre's rows, then one
                                              ALL_CENTRES row per gender
    combined/lshe_ALL_<YYYY-MM>_status.json   centres included, missing,
                                              partial-month and invalid files

The ALL_CENTRES rows add up each centre's CENTRE_TOTAL rows. Adding is safe
for every metric, reached_cumulative included, because each learner exists
on one centre server only.

Exit status: 0 if every expected centre is included, 1 if any is missing or
invalid, 2 for usage errors. Standard library only (Python 3.6+).
"""
import argparse
import csv
import io
import json
import os
import re
import sys
from collections import OrderedDict

METRICS = (
    "enrolled_learners",
    "active_learners",
    "sessions",
    "reached_new",
    "reached_cumulative",
    "completions",
    "video_watch_seconds",
)
COLUMNS = ("centre_code", "month", "class", "gender") + METRICS
GENDERS = ("MALE", "FEMALE", "NOT_SPECIFIED", "ALL")
CENTRE_TOTAL = "CENTRE_TOTAL"
ALL_CENTRES = "ALL_CENTRES"
CODE_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class InvalidReport(Exception):
    pass


def read_centres(path):
    """Centre codes from centres.conf, in file order."""
    codes = []
    with io.open(path, encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if line:
                code = line.split()[0]
                if CODE_RE.match(code) and code not in codes:
                    codes.append(code)
    return codes


def read_report(path, code, month):
    """Rows of one centre's CSV, checked against its file name."""
    with io.open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise InvalidReport("unexpected columns")
        rows = []
        for row in reader:
            if row["centre_code"] != code or row["month"] != month:
                raise InvalidReport("rows for a different centre or month")
            for metric in METRICS:
                if not row[metric].isdigit():
                    raise InvalidReport("non-numeric {}".format(metric))
            rows.append(row)
    if not any(r["class"] == CENTRE_TOTAL for r in rows):
        raise InvalidReport("no CENTRE_TOTAL rows")
    return rows


def month_complete(csv_path):
    meta = csv_path[: -len(".csv")] + ".json"
    try:
        with io.open(meta, encoding="utf-8") as f:
            return bool(json.load(f).get("month_complete", True))
    except (IOError, OSError, ValueError):
        return True  # no metadata: do not guess


def combine(month, collected, expected):
    found = sorted(
        d
        for d in os.listdir(collected)
        if CODE_RE.match(d) and os.path.isdir(os.path.join(collected, d))
    ) if os.path.isdir(collected) else []
    centres = list(expected) + [c for c in found if c not in expected]

    rows, included, missing, invalid, partial = [], [], [], {}, []
    totals = OrderedDict((g, dict.fromkeys(METRICS, 0)) for g in GENDERS)
    for code in centres:
        path = os.path.join(collected, code, "lshe_{}_{}.csv".format(code, month))
        if not os.path.isfile(path):
            if code in expected:
                missing.append(code)
            continue
        try:
            centre_rows = read_report(path, code, month)
        except (InvalidReport, csv.Error, UnicodeDecodeError) as e:
            invalid[code] = str(e)
            continue
        included.append(code)
        if not month_complete(path):
            partial.append(code)
        rows.extend(centre_rows)
        for row in centre_rows:
            if row["class"] == CENTRE_TOTAL and row["gender"] in totals:
                for metric in METRICS:
                    totals[row["gender"]][metric] += int(row[metric])

    for gender, figures in totals.items():
        row = {"centre_code": ALL_CENTRES, "month": month, "class": CENTRE_TOTAL, "gender": gender}
        row.update({m: str(v) for m, v in figures.items()})
        rows.append(row)

    status = {
        "month": month,
        "expected_centres": list(expected),
        "included_centres": included,
        "missing_centres": missing,
        "invalid_centres": invalid,
        "partial_month_centres": partial,
        "unexpected_centres": [c for c in included if c not in expected],
    }
    return rows, status


def write(rows, status, output_dir, month):
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    base = os.path.join(output_dir, "lshe_ALL_{}".format(month))
    with io.open(base + ".csv.tmp", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(base + ".csv.tmp", base + ".csv")
    with io.open(base + "_status.json", "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, sort_keys=True)
        f.write("\n")
    return base + ".csv"


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--month", required=True, help="YYYY-MM")
    parser.add_argument("--collected", default=os.path.join(here, "collected"))
    parser.add_argument("--centres", default=os.path.join(here, "centres.conf"))
    parser.add_argument("--output-dir", default=os.path.join(here, "combined"))
    args = parser.parse_args(argv)

    if not MONTH_RE.match(args.month):
        parser.error("--month must be YYYY-MM")
    if not os.path.isfile(args.centres):
        parser.error("centres file not found: {}".format(args.centres))

    expected = read_centres(args.centres)
    rows, status = combine(args.month, args.collected, expected)
    path = write(rows, status, args.output_dir, args.month)

    print("Wrote {} ({} centre(s) included)".format(path, len(status["included_centres"])))
    for key, label in (
        ("missing_centres", "Missing"),
        ("partial_month_centres", "Partial month (report run before the month ended)"),
        ("unexpected_centres", "Not in centres file"),
    ):
        if status[key]:
            print("{}: {}".format(label, ", ".join(status[key])))
    for code, reason in sorted(status["invalid_centres"].items()):
        print("Invalid report from {}: {}".format(code, reason))
    return 1 if status["missing_centres"] or status["invalid_centres"] else 0


if __name__ == "__main__":
    sys.exit(main())
