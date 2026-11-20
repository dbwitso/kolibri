# Where is what on an LSHE centre server

A map for troubleshooting: what runs, where its files and logs are, and
where to look when something is wrong. Run everything as root on the centre
server. To check the whole server in one go (read-only):

```sh
/opt/lshe/kolibri_helper_scripts/lshe/check_server.sh
```

## What runs

| What | Where | Started by |
| --- | --- | --- |
| Kolibri (web app) | container `lshe-kolibri`, port 8080 (and 8081 for zipped content) on `LSHE_BIND_IP` only | `lshe-kolibri.service` at boot ([Start on boot](deployment.md#start-on-boot)) |
| Database (PostgreSQL 13) | container `lshe-db`, inside Docker only | the same, with Kolibri |
| Nightly backup | `lshe/backup_db.sh` on the host | `lshe-backup.timer`, 01:30 Lusaka time |
| Monthly report | `lshe/run_monthly_report.sh` on the host | `lshe-report.timer`, 02:00 Lusaka time on the 1st |

Learners and coaches open `http://<LSHE_BIND_IP>:8080` (for example
`http://192.168.1.178:8080`). The server answers only on that address: not
on `localhost`, and not over NetBird.

## Where the files are

| Path | What | Notes |
| --- | --- | --- |
| `/opt/lshe/kolibri` | Kolibri source (branch `unesco_dev`) | `git pull` then rebuild to upgrade |
| `/opt/lshe/kolibri/docker/lshe/.env` | settings: centre code, bind address, passwords, MindSpark connection | **secret**: never copy off the server or commit |
| `/opt/lshe/kolibri/docker/lshe/docker-compose.yml` | containers, ports, folders | |
| `/opt/lshe/kolibri_helper_scripts` | helper scripts (branch `develop`) | mounted read-only in Kolibri at `/opt/kolibri_helper_scripts` |
| `/srv/lshe-content` | channel packs to import | read-only in Kolibri |
| `/srv/lshe-export` | channel packs made from this server | `export_channels.sh` |
| `/srv/lshe-reports` | monthly report files (`lshe_<CENTRE>_<YYYY-MM>.csv/.json`) | counts only, no names |
| `/srv/lshe-backups` | database backups: `*_nightly.dump` (14 days) and `*_before_import.dump` (kept) | **learner data**: root only |
| Docker volume `lshe_kolibrihome` | Kolibri's home: imported content, Kolibri's own logs | `docker exec lshe-kolibri ls /kolibrihome` |
| Docker volume `lshe_pgdata` | the database files | back up with `backup_db.sh`, never copy by hand |

## Where the logs are

| Log | What |
| --- | --- |
| `docker logs --tail 100 lshe-kolibri` | Kolibri: every page request, and errors (`Traceback`, `" 500 "`) |
| `docker logs --tail 50 lshe-db` | the database |
| `journalctl -u lshe-kolibri.service -b` | start-up at this boot (waiting for the network address) |
| `/var/log/lshe/backup.log` | nightly backups |
| `/var/log/lshe/report.log` | monthly reports |
| `/var/log/lshe/content.log` | `get_content.sh`, `export_channels.sh` |
| `/var/log/lshe/channels.log` | `import_channels.sh` |
| `/var/log/lshe/import.log` | MindSpark roster imports |
| `docker exec lshe-kolibri ls /kolibrihome/logs` | Kolibri's own log files |

## The helper scripts

All in `/opt/lshe/kolibri_helper_scripts/lshe/`. Each prints its usage with
`--help`. The `.sh` scripts run on the host; the `.py` scripts run inside
Kolibri, through `./run_script.sh <script>.py`.

| Task | Command |
| --- | --- |
| Check the whole server | `./check_server.sh` |
| What content is on the server | `./run_script.sh content_status.py --files` |
| Find a channel pack on a USB drive | `./get_content.sh --find` |
| Copy, check and import a pack from a USB drive | `./get_content.sh --from /media/<drive>/<pack> --import` |
| The same from another server over SSH | `./get_content.sh --from-ssh root@<server>:/srv/lshe-export/<pack> --import` |
| Import from a distribution server (not another centre server) | `./import_channels.sh --network http://<server>:8080 --file channels.conf` |
| Make a pack of this server's channels (e.g. on a USB drive) | `./export_channels.sh --all --to /media/<drive>` |
| Grade bands of classes and channels | `./run_script.sh set_class_band.py --list` |
| Import learners from MindSpark | `./run_import.sh --org-id <ORG>` (dry run), then `--apply` |
| Back up now | `./backup_db.sh` |
| Write a month's report | `./run_monthly_report.sh 2026-11` |

## Something is wrong: where to look

| Symptom | Look at | Usual fix |
| --- | --- | --- |
| Tablets cannot open Kolibri | `systemctl status lshe-kolibri.service`; `docker ps`; `curl -I http://<LSHE_BIND_IP>:8080/` | Tablet on another Wi-Fi; server's address changed (match `LSHE_BIND_IP`); `systemctl restart lshe-kolibri.service` |
| Kolibri did not start after a power cut | `journalctl -u lshe-kolibri.service -b` | "address … is not on this server": the network is not up yet; it retries every minute |
| "Server Error (500)" on every page | `docker logs --tail 50 lshe-kolibri` | A plugin enabled whose frontend was not built is disabled automatically at start; otherwise rebuild: `docker compose up -d --build` |
| Learners see "Ask your coach for a lesson" | the class's lessons in Plan | No visible lesson for their class: the coach makes one visible |
| A class cannot be given lessons | `./run_script.sh set_class_band.py --list` | The class has no band: `set_class_band.py --class "<name>" --band G4-5` |
| A video says it is locked | the learner's lesson report (Reports) | Finished videos lock; the coach presses Unlock |
| A channel is incomplete or a video will not play | `./run_script.sh content_status.py --files` | Import it again: `./import_channels.sh <channel id>` (or `get_content.sh` first) |
| Content import fails | `/var/log/lshe/channels.log`, `/var/log/lshe/content.log` | Pack damaged: run `get_content.sh` again (it re-copies damaged files); not enough space: `df -h /srv` |
| No monthly report on the 1st | `/var/log/lshe/report.log`; `systemctl list-timers 'lshe-*'` | Run it by hand: `./run_monthly_report.sh <YYYY-MM>` |
| No backup last night | `/var/log/lshe/backup.log` | Disk full, or the database container down; run `./backup_db.sh` |
| Disk filling up | `df -h / /srv`; `du -sh /srv/*` | Old exports in `/srv/lshe-export` can be deleted; never delete `pgdata` |

## Changing things safely

- **Upgrade:** `cd /opt/lshe/kolibri && git pull && git lfs pull && cd docker/lshe && docker compose up -d --build`, and `git pull` in the helper scripts. Take a backup first (`backup_db.sh`).
- **Stop for maintenance:** `systemctl stop lshe-kolibri.service`; start again with `systemctl start lshe-kolibri.service`.
- **Restore a backup:** [deployment.md, Backup and restore](deployment.md#backup-and-restore).
- **Settings:** edit `.env`, then `docker compose up -d` in `docker/lshe`.
