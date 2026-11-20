# LSHE centre server: deployment

This guide is for whoever installs and runs a centre server for the Life
Skills and Health Education (LSHE) pilot. It assumes Linux server experience
and some Docker. Nothing in it depends on a particular provider.

## What a centre server does

- One Kolibri server per centre carries the UNESCO/MoE-approved LSHE channels
  for Grade 4–7 learners, plus the teacher channels.
- It works **fully offline**. Learners use tablets that open the server in a
  web browser over the centre's Wi-Fi. No tablet runs Kolibri, and no Kolibri
  server syncs with any other.
- Learners and classes come from the centre's MindSpark roster, which is
  read-only (see [roster-import.md](roster-import.md)).
- Each month the server writes one report file of aggregate figures. The
  provider collects these remotely (see [reporting.md](reporting.md)).

## Hardware and network

| Item | Requirement |
| --- | --- |
| Server | 64-bit x86 PC or small server; 4 or more CPU cores; 8 GB RAM minimum (16 GB recommended); SSD |
| Storage | Room for all imported channels, plus at least the same again for database backups and a spare copy of the channel packs |
| Power | A UPS sized to allow a clean shutdown; the server should start Kolibri automatically on boot |
| Network | Server cabled to the Wi-Fi access point or switch; a fixed LAN address (static, or a DHCP reservation) |
| Wi-Fi | An access point rated for the number of tablets that will be used at once. A full class streaming video at the same time is the usual peak (see the acceptance checklist) |
| Tablets | A current web browser (Chrome or Firefox). Nothing to install |
| Remote access | Optional: a VPN overlay (for example NetBird) for support and report collection. The centre needs no internet connection for teaching |

Estimate peak bandwidth as learners streaming at once × the bitrate of the
LSHE videos. Confirm it with the "full class streams at once" test in
[acceptance-checklist.md](acceptance-checklist.md) before learners start.

### Ports

| Port | Used by | Reachable from |
| --- | --- | --- |
| 8080 | Kolibri: pages, API, videos and other media (`/content/storage/`) | Centre LAN |
| 8081 (`LSHE_ZIP_PORT`) | Kolibri's sandboxed server for zipped HTML5 and H5P content. Set another port if 8081 is already used on the server | Centre LAN |
| 22 | SSH for support and report collection | VPN only |

PostgreSQL is not exposed. Both Kolibri ports are bound to the server's LAN
address only (`LSHE_BIND_IP`). Docker-published ports bypass host firewalls
such as UFW, so that binding is what keeps them off other interfaces.

## Install

1. Install Docker Engine with the Compose plugin. Setting the host timezone
   to Africa/Lusaka (`sudo timedatectl set-timezone Africa/Lusaka`) is
   optional. Kolibri, the reports and the report timer use Lusaka time
   whatever the host's zone is, so leave it alone if other software on the
   server depends on it.
2. Get the source at the release tag to deploy, for example
   `git clone <repository> /opt/lshe/kolibri && cd /opt/lshe/kolibri && git checkout <tag>`.
3. Create the host folders, and get the helper scripts at the matching
   release:
   `sudo mkdir -p /srv/lshe-reports /srv/lshe-content /srv/lshe-backups /var/log/lshe`,
   then
   `git clone <helper scripts repository> /opt/lshe/kolibri_helper_scripts`.
   The compose file mounts that folder into the Kolibri container. If it is
   somewhere else, set `LSHE_HELPER_SCRIPTS_DIR` in `.env` (step 6).
4. Check that ports 8080 and 8081 are free:
   `sudo ss -ltnp | grep -E ':(8080|8081)\b'`. If 8081 is taken, choose
   another port for `LSHE_ZIP_PORT` in the next step.
5. Build the base image, from the repository root:
   `docker build -f docker/base.dockerfile -t learningequality/kolibribase .`.
   It is not available from a registry. Rebuild it when the Python or
   JavaScript requirements change.
6. `cd docker/lshe && cp .env.example .env && chmod 600 .env`, then fill in
   every value. `.env` holds passwords, so it must never be committed or
   copied off the server. It is kept out of the Docker images.
7. `docker compose up -d --build`. The first build compiles the frontend, so
   allow plenty of time. On first start, the facility and superuser from
   `.env` are created, with the formal preset.
8. Open `http://<LSHE_BIND_IP>:8080` from a tablet.
9. Make Kolibri start on boot: see [Start on boot](#start-on-boot).

[`docker/lshe/README.md`](../../docker/lshe/README.md) covers the MindSpark
connection and firewall settings. kolibri_helper_scripts' `lshe/README.md`
covers the scripts, the report timer and the read-only report-collection
account.

## Start on boot

After a power cut or a reboot, Kolibri starts by itself, with no command.
The containers' `restart: unless-stopped` is not enough on its own: Kolibri
listens only on `LSHE_BIND_IP`, and at boot Docker can start before the
network has that address, so the ports cannot be bound and Docker does not
retry. A container stopped by hand (`docker compose stop`) also stays stopped
after a reboot. `lshe-kolibri.service` (in `docker/lshe/`) waits for the
address (`wait-for-address.sh`, up to two minutes), runs `docker compose up
-d`, and tries again every minute if that fails.

Install once, as root:

```sh
systemctl enable docker                    # Docker itself starts on boot
cd /opt/lshe/kolibri/docker/lshe
cp lshe-kolibri.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now lshe-kolibri.service
systemctl status lshe-kolibri.service --no-pager
```

If the Kolibri checkout is not `/opt/lshe/kolibri`, edit the two paths in
the copied service file first.

**Check it** with a reboot (`reboot`), then, without starting anything:

```sh
systemctl status lshe-kolibri.service --no-pager   # active (exited)
docker compose -f /opt/lshe/kolibri/docker/lshe/docker-compose.yml ps
curl -s -o /dev/null -w "%{http_code}\n" http://<LSHE_BIND_IP>:8080/   # 302
```

Kolibri can take a minute or two after boot to answer.

**If it did not start:** `journalctl -u lshe-kolibri.service -b --no-pager`
shows this boot's attempts. "address … is not on this server" means the
network (cable, Wi-Fi, or the address in `LSHE_BIND_IP`) is not up; the
service keeps trying every minute. Anything else: `docker logs --tail 50
lshe-kolibri`.

To stop Kolibri for maintenance, use `systemctl stop lshe-kolibri.service`
(the containers stop too); `systemctl start lshe-kolibri.service` starts it
again. Upgrades still use `docker compose up -d --build` (see below).

## Provisioning (formal preset)

The facility must use Kolibri's **formal** preset: learners sign in with their
username and no password, and only admins create accounts. The compose file
sets `KOLIBRI_PROVISIONDEVICE_PRESET=formal`. If `.env` sets
`KOLIBRI_PROVISIONDEVICE_FACILITY`, the facility and device superuser are
created on first start. Otherwise complete Kolibri's setup wizard and choose
the formal ("schools") option.

Then check, as the superuser, under **Facility → Settings**:

- learners can sign in with no password;
- learners cannot edit their own name, username or password;
- guest access is off.

The superuser is for installers and support only, not for teachers.

## Channels

LSHE channels (and any teacher channels) travel as **channel packs**: a
folder with `content/databases`, `content/storage` and a `channels.conf`
listing the channel IDs, names and bands. The helper scripts are in
`/opt/lshe/kolibri_helper_scripts/lshe`:

```sh
./get_content.sh --find                                   # packs on a plugged-in USB drive
./get_content.sh --from /media/<drive>/<pack> --import    # from a USB drive
./get_content.sh --from-ssh root@<server>:/srv/lshe-export/<pack> --import   # from another machine
./export_channels.sh --all --to /media/<drive>            # make a pack of this server's channels
./run_script.sh content_status.py --files                 # what the server has
```

`get_content.sh` copies the pack into `/srv/lshe-content` (resuming if
interrupted), checks every file against its checksum, and with `--import`
runs `import_channels.sh` (Kolibri's `importchannel` and `importcontent`, in
the container). Re-running is safe. Logs: `/var/log/lshe/content.log` and
`/var/log/lshe/channels.log`. The packs for a first install are built with
kolibri_helper_scripts' `lshe/content/build_offline_channels.sh`.

**Between two centre servers, use a pack (USB, or `--from-ssh`), not
`import_channels.sh --network`.** LSHE servers switch off Kolibri's public
content API (see "Content lockdown" below), so one centre server cannot
import from another over the network. `--network` works only from a
distribution server that isn't running in LSHE mode.

Put the teacher channels' IDs in `LSHE_TEACHER_CHANNEL_IDS` in `.env`, comma
separated, and restart (`docker compose up -d`). Those channels are then
never assignable to learners, never shown to them, and left out of reports.

## Grade bands

Each class belongs to one grade band, and each band allows a list of
channels. Coaches can only assign content from their class's band. Learners
only ever see assigned content from their band's channels. A class with no
band can be assigned nothing.

```sh
cd /opt/lshe/kolibri_helper_scripts/lshe
sudo ./run_script.sh set_band_channels.py --band G4-5 <channel_id> [<channel_id> ...]   # replaces the list
sudo ./run_script.sh set_band_channels.py --band G6-7 <channel_id> [<channel_id> ...]
sudo ./run_script.sh set_class_band.py --class "Grade 4 A" --band G4-5
sudo ./run_script.sh set_class_band.py --class "Grade 6 A" --band G6-7
sudo ./run_script.sh set_class_band.py --list    # bands, channels, and classes with no band
```

`set_class_band.py --class-id <id>` is for classes that share a name.
`set_band_channels.py` refuses teacher channels. Set up bands after the
roster import has created the classes, and before teachers start assigning.
The bands are stored in Kolibri's database, and Kolibri enforces them. The
scripts only set them.

Grade bands and the content lockdown are on unless `LSHE_GRADE_BANDS=off`,
which is only for servers outside the LSHE pilot.

## Teachers

Each teacher (around 50 across the pilot) is a **class coach** for their own
class only, never a facility admin or facility coach. A class coach sees
only the classes they are assigned to, along with all channels, the teacher
channels included.

To create a teacher, sign in as a facility admin:

1. **Facility → Users → New user**. Enter the name and a username. Set
   **User type** to **Coach**, then choose **Class coach**. Give a password:
   coaches sign in with a password even in the formal preset.
2. **Facility → Classes →** the teacher's class **→ Assign coaches**, and
   select the teacher.

Check by signing in as the teacher: the Coach page should list only that
class. To move a teacher to another class, remove them from the old class's
coaches and add them to the new one.

## Assessments

Adaptive assessments, a fork feature outside the LSHE content, are switched
off on LSHE servers (`LSHE_DISABLE_ASSESSMENTS=true`). Their API refuses all
requests. Lessons and quizzes work as normal.

## Content lockdown and known limitations

With grade bands on, the server also:

- shows signed-out visitors no content at all;
- filters channel lists, file lists and the knowledge map down to what a
  learner may see;
- switches off the public content API that other Kolibri servers use to
  import from it.

**Known limitation: direct file URLs.** Kolibri serves media files
(`/content/storage/…` on port 8080) and zipped HTML5/H5P content (port 8081)
without checking who is asking. Anyone who has a file's URL can download it,
signed in or not. The URL contains the file's content checksum, which can't
be guessed. On LSHE servers, the only routes that hand out those checksums
are a learner's own assigned content and the coach and admin pages. The
remaining risk is a URL being passed on, for example a coach sharing a
link, or a learner keeping one from content they were once assigned.
Checking every file request would add a database lookup to each video
range request and would need the long browser caching removed. That has
not been done, so treat file URLs as shareable.

## Backup and restore

Back up before every upgrade or roster import (`lshe/run_import.sh --apply`
does this itself), and every night: kolibri_helper_scripts'
`lshe/backup_db.sh`, run by its `lshe-backup.timer` at 01:30 Lusaka time,
dumps the database, checks the dump and keeps 14 days (set-up in that
repository's `lshe/README.md`, "Nightly database backup"). By hand:

```sh
docker exec lshe-db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
  > /srv/lshe-backups/kolibri_$(date +%Y%m%d_%H%M%S).dump
chmod 600 /srv/lshe-backups/*.dump
```

Also keep: `docker/lshe/.env` (in a secure place, as it holds passwords),
the channel packs used for import, and `/srv/lshe-reports`. Imported channel
content can be re-imported from the packs and need not be backed up.

The backups contain learners' personal data. Keep them on the server or on
encrypted media, and delete them under the retention rules in
[data-protection.md](data-protection.md).

To restore a database backup:

```sh
cd /opt/lshe/kolibri/docker/lshe
docker compose stop kolibri
docker exec lshe-db sh -c 'dropdb -U "$POSTGRES_USER" "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'
docker exec -i lshe-db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner' < /srv/lshe-backups/<file>.dump
docker compose start kolibri
```

## Upgrades and rollback

1. Back up the database (above).
2. `git fetch && git checkout <new tag>`, then `docker compose up -d --build`.
   Kolibri applies database migrations on start. Update the helper scripts
   to the matching release too (`git pull` in
   `/opt/lshe/kolibri_helper_scripts`): they use Kolibri's models, so keep
   the two in step.
3. Run the relevant checks from the acceptance checklist.

Migrations only run forward. To roll back, check out the previous tag,
restore the database backup taken before the upgrade, then
`docker compose up -d --build`. Don't reverse migrations by hand: reversing
the `kolibri.plugins.edulution` migrations deletes the grade band setup and
the saved monthly class snapshots.
