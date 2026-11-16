# Monthly LSHE reporting

Every centre server writes one file of aggregate figures per month. The
provider collects the files from all centres and combines them into one
programme-wide file per month. The files contain **no personal data**: no
names, usernames, birth years or per-learner rows.

## Who is counted

- **Learners only:** accounts with no role (not a coach, facility coach or
  admin) that are not the device superuser. Teacher and admin activity is
  never counted.
- **LSHE content only:** activity in the teacher channels
  (`LSHE_TEACHER_CHANNEL_IDS`) is left out of every figure.

## Metrics

Each centre file has one row per class and gender (`MALE`, `FEMALE`,
`NOT_SPECIFIED`, and `ALL`), plus `CENTRE_TOTAL` rows. Learners with no class
appear under `NO_CLASS`. A learner in two classes counts in both classes,
but only once in the centre total.

| Column | Definition |
| --- | --- |
| `enrolled_learners` | Learners in the class at the end of the month |
| `active_learners` | Learners with at least one session starting in the month |
| `sessions` | Sessions starting in the month |
| `reached_new` | Learners whose **first** fully completed LSHE item (progress = 1) falls in the month |
| `reached_cumulative` | Learners with at least one fully completed LSHE item by the end of the month. This is the UNESCO definition of *reached*: one approved content piece completed in full |
| `completions` | LSHE items reaching full completion in the month |
| `video_watch_seconds` | Time spent in LSHE video sessions that ended in the month |

A video counts as completed when Kolibri records it as fully watched
(progress = 1). Half a video is not a completion and does not make a learner
"reached", but its viewing time counts in `video_watch_seconds`.

Watch time is taken from the per-session logs, not the per-item totals, so
each month gets only its own viewing.

## Month boundaries and re-runs

- Months run from midnight on the 1st to midnight on the 1st of the next
  month, **Africa/Lusaka time** (`LSHE_REPORT_TIMEZONE`). This doesn't depend
  on the server's clock settings, and the timezone is recorded in each file's
  metadata.
- **Re-running a month overwrites its file with the same figures.** Kolibri
  doesn't record when learners move between classes. So the first time a
  finished month is reported, each learner's class and gender for that month
  is saved, and later runs use that record. Moving a learner in April
  doesn't change March's report.
- A report for the current, unfinished month is allowed but partial. It is
  marked `month_complete: false` and doesn't save the class record.

## Files

On each centre server, in `/srv/lshe-reports`:

- `lshe_<CENTRE_CODE>_<YYYY-MM>.csv`: columns `centre_code, month, class,
  gender`, then the metrics above.
- `lshe_<CENTRE_CODE>_<YYYY-MM>.json`: metadata, including generation time,
  Kolibri version, facility ID, timezone, month start and end, whether the
  month was complete, when the class record was taken, the excluded teacher
  channels, and the metric definitions.

`CENTRE_CODE` is the server's `KOLIBRI_CENTRE_CODE` setting. The report
refuses to run without it.

## Schedule

A systemd timer on each centre server runs the report for the previous month
on the **1st of each month at 02:00 Lusaka time**, whatever time zone the
server's clock uses. If the server is off at
that time, the report runs when it next starts. To run it by hand:

```sh
sudo /opt/lshe/kolibri/docker/lshe/run_monthly_report.sh            # previous month
sudo /opt/lshe/kolibri/docker/lshe/run_monthly_report.sh 2027-03    # a given month
```

The log is at `/var/log/lshe/report.log`.

## Collection

On the provider's central machine, `docker/lshe/central/collect_reports.sh`
pulls each centre's report files over the VPN with `rsync` over SSH. The
list of centres is in `centres.conf`: code, host, and optionally the port
and user.

On each centre, the account it uses (`lshe-reports`) is limited by its SSH
key to **read-only** access to `/srv/lshe-reports`. It can't open a shell,
write anything or read anything else. Setup is in
`docker/lshe/README.md`.

A centre that can't be reached is logged and skipped, and the others still
run. The script ends with an error status if any centre failed, so the
provider's scheduler can raise an alert. Collected files are never deleted
centrally, even if a centre loses them.

## Combining

```sh
python3 docker/lshe/central/combine_reports.py --month 2027-03
```

This writes `combined/lshe_ALL_2027-03.csv`, with every centre's rows plus
`ALL_CENTRES` totals per gender, and `combined/lshe_ALL_2027-03_status.json`.

The totals add up the centres' `CENTRE_TOTAL` rows. Adding works for every
metric, `reached_cumulative` included, because each learner is on one centre
server only.

The status file and the script's output list:

- **missing centres:** in `centres.conf` but no report for the month;
- **invalid** files, for example the wrong month or centre code inside;
- **partial-month** reports, run before the month ended;
- centres that reported but are not in `centres.conf`.

The script exits with an error status when any centre is missing or
invalid. Chase missing centres, then re-run: combining is repeatable.
