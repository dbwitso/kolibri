# LSHE deployment files

Docker setup and scripts for an LSHE (Life Skills and Health Education)
centre server, and for collecting monthly reports centrally. The full
procedures are in [`docs/lshe/`](../../docs/lshe/); this page covers what each
file is for and the host settings they rely on.

| File | Runs on | Purpose |
| --- | --- | --- |
| `docker-compose.yml` | centre server | Kolibri and PostgreSQL |
| `.env.example` | centre server | Settings template. Copy it to `.env` (git-ignored). |
| `run_monthly_report.sh` | centre server | Writes the previous month's report |
| `systemd/lshe-report.{service,timer}` | centre server | Runs the report on the 1st at 02:00 |
| `run_import.sh` | centre server | MindSpark roster import: dry run, backup, then `--apply` |
| `mindspark_class_probe.js` | MindSpark server | Shows how learners link to classes, without personal data |
| `central/collect_reports.sh` | central machine | Pulls report files from every centre |
| `central/combine_reports.py` | central machine | One file per month, all-centre totals, missing centres |
| `central/centres.conf.example` | central machine | List of centres |

## Centre server

### First start

```sh
sudo timedatectl set-timezone Africa/Lusaka
sudo mkdir -p /srv/lshe-reports /srv/lshe-content /srv/lshe-backups /var/log/lshe
# From the repository root: build the base image once per server. It is not
# on Docker Hub. Rebuild it when requirements/ or package.json change.
docker build -f docker/base.dockerfile -t learningequality/kolibribase .
cd docker/lshe
cp .env.example .env && chmod 600 .env   # then fill in every value
docker compose up -d --build
```

The compose file refuses to start until `.env` sets the database password,
the superuser password, `KOLIBRI_CENTRE_CODE` and `LSHE_BIND_IP`. Without a
superuser password, `docker/entrypoint.py` would use its default
(`admin123`).

### Ports and firewall

- Tablets need **8080** (Kolibri, including videos) and the zip content port
  (`LSHE_ZIP_PORT`, default **8081**, for zipped HTML5 and H5P content) on the
  centre LAN. Both are published on `LSHE_BIND_IP` only.
- If something else on the server already uses 8081 (for example a
  Guacamole gateway), set `LSHE_ZIP_PORT` to a free port such as 8082. Kolibri
  tells browsers this port, so it is used unchanged inside and outside the
  container. Check first with `sudo ss -ltnp | grep -E ':(8080|8081)\b'`.
- **Docker-published ports bypass UFW.** Docker writes its own iptables rules,
  so `ufw deny 8080` has no effect. Binding to `LSHE_BIND_IP` is what keeps
  the ports off the NetBird and other interfaces. If you also need UFW rules
  for published ports, add them to the `DOCKER-USER` chain.
- PostgreSQL is not published.

### Reaching MindSpark (MongoDB)

Inside the container, `127.0.0.1` is the container itself, not the host.

**MongoDB on this same server** (installed natively): if `mongod` already
listens on all interfaces (`bindIp: 0.0.0.0`), use the gateway address of
Kolibri's Docker network, `172.30.50.1` (with the default
`LSHE_DOCKER_SUBNET`), in `MINDSPARK_MONGO_URI`. It doesn't change when the
server's LAN address does. Make sure MongoDB has `security.authorization:
enabled`, because a `0.0.0.0` binding exposes it to every network the server
is on. Then skip to step 3 below (the read-only user).

**MongoDB on another machine:** set `MINDSPARK_MONGO_URI` to that machine's
LAN address. On the MindSpark server:

1. `mongod.conf` → `net.bindIp` must include that LAN address, e.g.
   `bindIp: 127.0.0.1,192.168.1.10`. Restart `mongod`.
2. Allow only the Kolibri containers' subnet (`LSHE_DOCKER_SUBNET`, default
   `172.30.50.0/24`) when MongoDB is on the same box, or only the Kolibri
   server's address otherwise:
   `sudo ufw allow from 172.30.50.0/24 to any port 27017 proto tcp`
3. Create a read-only user and put it in the URI:

   ```js
   db.getSiblingDB("admin").createUser({
     user: "kolibri_reader",
     pwd: passwordPrompt(),
     roles: [
       { role: "read", db: "UserManagement" },
       { role: "read", db: "UserAuthentication" },
     ],
   })
   ```

Check it from the server with
`docker exec lshe-kolibri kolibri manage importfrommindspark --dryrun`.

### Monthly report timer

```sh
sudo cp systemd/lshe-report.service systemd/lshe-report.timer /etc/systemd/system/
# edit ExecStart in lshe-report.service if the repository is not in /opt/lshe/kolibri
sudo systemctl daemon-reload
sudo systemctl enable --now lshe-report.timer
systemctl list-timers lshe-report.timer
```

`Persistent=true` makes a missed run (server off at 02:00 on the 1st) happen
at the next boot. To run by hand: `sudo ./run_monthly_report.sh [YYYY-MM]`.
Re-running a month overwrites its file with the same figures. The log is in
`/var/log/lshe/report.log`.

As a cron alternative to the timer:
`0 2 1 * * /opt/lshe/kolibri/docker/lshe/run_monthly_report.sh`.

### Read-only user for report collection

The central machine connects as `lshe-reports`, which can only read
`/srv/lshe-reports`:

```sh
sudo adduser --system --group --shell /bin/sh lshe-reports
sudo chgrp -R lshe-reports /srv/lshe-reports && sudo chmod -R g+rX,o-rwx /srv/lshe-reports
sudo install -d -m 700 -o lshe-reports -g lshe-reports ~lshe-reports/.ssh
# One line in ~lshe-reports/.ssh/authorized_keys (the central machine's public key):
#   command="rrsync -ro /srv/lshe-reports",restrict ssh-ed25519 AAAA... lshe-central
```

`rrsync` comes with rsync. On older Ubuntu releases it is
`/usr/share/doc/rsync/scripts/rrsync` and needs copying to `/usr/local/bin`.
With this key restriction, the user can't open a shell, write files or read
anything outside `/srv/lshe-reports`.

### Roster import

```sh
./run_import.sh --org-id <ORG>                    # dry run: counts only
./run_import.sh --apply --org-id <ORG>            # backup, then import
./run_import.sh --apply --org-id <ORG> --remove-inactive   # end of term
```

Backups go to `/srv/lshe-backups`, and the log to `/var/log/lshe/import.log`.

## Central machine

```sh
cd docker/lshe/central
cp centres.conf.example centres.conf   # one line per centre
LSHE_SSH_KEY=~/.ssh/lshe_reports ./collect_reports.sh
python3 combine_reports.py --month 2027-03
```

`collect_reports.sh` skips a centre it can't reach, carries on with the
rest, and exits non-zero if any centre failed. `combine_reports.py` writes
`combined/lshe_ALL_<month>.csv` and `combined/lshe_ALL_<month>_status.json`.
It also lists centres that are missing, invalid, or that reported a partial
month.

Tests: `python3 -m pytest central/test_combine_reports.py`.
