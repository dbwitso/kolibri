# LSHE deployment files

Docker set-up for an LSHE (Life Skills and Health Education) centre server:
Edulution's Kolibri and PostgreSQL. The full procedures are in
[`docs/lshe/`](../../docs/lshe/). This page covers what each file is for and
the host settings they rely on.

| File | Purpose |
| --- | --- |
| `docker-compose.yml` | Kolibri and PostgreSQL |
| `.env.example` | Settings template. Copy it to `.env` (git-ignored). |

The scripts that run a centre are in the separate **kolibri_helper_scripts**
repository, in `lshe/`: the MindSpark roster import, channel import, grade
bands, the monthly report and its timer, and central report collection. The
compose file mounts that repository, read-only, into the Kolibri container at
`/opt/kolibri_helper_scripts`. Its shell scripts run on the host and call its
Python scripts inside the container. See `lshe/README.md` there.

## Centre server

### First start

```sh
# Optional: the report timer and the containers use Africa/Lusaka whatever
# the host's zone is, so leave the host zone alone if other software on the
# server (for example MindSpark) depends on it.
sudo timedatectl set-timezone Africa/Lusaka
sudo mkdir -p /srv/lshe-reports /srv/lshe-content /srv/lshe-backups /var/log/lshe
# The helper scripts, mounted into the container (LSHE_HELPER_SCRIPTS_DIR).
sudo git clone -b develop https://github.com/dbwitso/kolibri_helper_scripts.git /opt/lshe/kolibri_helper_scripts
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

If `/opt/lshe/kolibri_helper_scripts` doesn't exist when the containers
start, Docker creates it empty and the helper scripts report that they
can't find their files. Clone the repository (or set
`LSHE_HELPER_SCRIPTS_DIR` to where it is), then run `docker compose up -d`
again.

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
is on.

**MongoDB on another machine:** set `MINDSPARK_MONGO_URI` to that machine's
LAN address. On the MindSpark server, `mongod.conf` → `net.bindIp` must
include that address (for example `bindIp: 127.0.0.1,192.168.1.10`), and the
firewall should allow port 27017 from the Kolibri server only.

In both cases, use **MindSpark's existing login** in the URI. The import only
reads `UserManagement` and `UserAuthentication`. Don't create or change
MindSpark users, and don't write to MindSpark.

Check the connection with a dry run, which changes nothing:
`sudo /opt/lshe/kolibri_helper_scripts/lshe/run_import.sh`.

### Scripts

Everything run on a schedule or by hand is in kolibri_helper_scripts
(`lshe/README.md`):

| Task | Script (in `/opt/lshe/kolibri_helper_scripts/lshe`) |
| --- | --- |
| Import learners and classes from MindSpark | `run_import.sh` (dry run), `run_import.sh --apply` |
| Import channels | `import_channels.sh --file channels.conf` |
| Grade bands | `run_script.sh set_band_channels.py …`, `run_script.sh set_class_band.py …` |
| Monthly report | `run_monthly_report.sh`, run by `systemd/lshe-report.timer` |
| Central report collection | `central/collect_reports.sh`, `central/combine_reports.py` |
