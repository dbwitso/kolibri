"""
Tests for combine_reports.py (standard library only):

    python3 -m pytest docker/lshe/central/test_combine_reports.py
"""
import csv
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import combine_reports as cr  # noqa: E402

MONTH = "2027-03"


def centre_rows(code, reached, month=MONTH, extra_class=True):
    rows = []
    classes = (["Grade 5 A"] if extra_class else []) + [cr.CENTRE_TOTAL]
    for cls in classes:
        for gender in cr.GENDERS:
            row = {"centre_code": code, "month": month, "class": cls, "gender": gender}
            row.update({m: "1" for m in cr.METRICS})
            row["reached_cumulative"] = str(reached[gender])
            rows.append(row)
    return rows


def write_centre(collected, code, rows, complete=True):
    d = os.path.join(collected, code)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "lshe_{}_{}.csv".format(code, MONTH))
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cr.COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    with io.open(path[:-4] + ".json", "w") as f:
        json.dump({"month_complete": complete}, f)


def write_conf(tmp_path, codes):
    path = tmp_path / "centres.conf"
    path.write_text("# comment\n\n" + "\n".join("{} host.example".format(c) for c in codes) + "\n")
    return str(path)


def run(tmp_path, codes):
    out = tmp_path / "combined"
    status = cr.main(
        ["--month", MONTH, "--collected", str(tmp_path / "collected"),
         "--centres", write_conf(tmp_path, codes), "--output-dir", str(out)]
    )
    with io.open(str(out / "lshe_ALL_{}.csv".format(MONTH)), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with io.open(str(out / "lshe_ALL_{}_status.json".format(MONTH))) as f:
        return status, rows, json.load(f)


def totals(rows):
    return {
        r["gender"]: int(r["reached_cumulative"])
        for r in rows
        if r["centre_code"] == cr.ALL_CENTRES
    }


def test_combines_and_sums_reached_cumulative(tmp_path):
    collected = str(tmp_path / "collected")
    write_centre(collected, "C1", centre_rows("C1", {"MALE": 3, "FEMALE": 4, "NOT_SPECIFIED": 0, "ALL": 7}))
    write_centre(collected, "C2", centre_rows("C2", {"MALE": 1, "FEMALE": 2, "NOT_SPECIFIED": 1, "ALL": 4}))
    status, rows, meta = run(tmp_path, ["C1", "C2"])
    assert status == 0
    assert totals(rows) == {"MALE": 4, "FEMALE": 6, "NOT_SPECIFIED": 1, "ALL": 11}
    # Class rows are carried through but not added to the totals twice.
    assert sum(1 for r in rows if r["centre_code"] == "C1") == 8
    assert meta["missing_centres"] == []
    assert meta["included_centres"] == ["C1", "C2"]


def test_lists_missing_centres(tmp_path):
    collected = str(tmp_path / "collected")
    write_centre(collected, "C1", centre_rows("C1", dict.fromkeys(cr.GENDERS, 1)))
    status, rows, meta = run(tmp_path, ["C1", "C2", "C3"])
    assert status == 1
    assert meta["missing_centres"] == ["C2", "C3"]
    assert totals(rows)["ALL"] == 1


def test_rejects_file_for_wrong_month(tmp_path):
    collected = str(tmp_path / "collected")
    write_centre(collected, "C1", centre_rows("C1", dict.fromkeys(cr.GENDERS, 1), month="2027-02"))
    status, rows, meta = run(tmp_path, ["C1"])
    assert status == 1
    assert "C1" in meta["invalid_centres"]
    assert totals(rows)["ALL"] == 0


def test_flags_partial_month_and_unexpected_centre(tmp_path):
    collected = str(tmp_path / "collected")
    write_centre(collected, "C1", centre_rows("C1", dict.fromkeys(cr.GENDERS, 1)), complete=False)
    write_centre(collected, "C9", centre_rows("C9", dict.fromkeys(cr.GENDERS, 1)))
    status, rows, meta = run(tmp_path, ["C1"])
    assert meta["partial_month_centres"] == ["C1"]
    assert meta["unexpected_centres"] == ["C9"]
    assert totals(rows)["ALL"] == 2


def test_rerun_is_identical(tmp_path):
    collected = str(tmp_path / "collected")
    write_centre(collected, "C1", centre_rows("C1", dict.fromkeys(cr.GENDERS, 2)))
    _, first, _ = run(tmp_path, ["C1"])
    _, second, _ = run(tmp_path, ["C1"])
    assert first == second
