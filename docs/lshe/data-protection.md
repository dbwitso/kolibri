# Data protection

LSHE learners are children. Each centre server stores the minimum personal
data needed to sign learners in, show them their lessons and give teachers
their class's progress. No personal data leaves the centre server: the
monthly reports are aggregate figures only.

## What personal data is stored

All of it is on the centre server, in the PostgreSQL database
(`lshe_pgdata` Docker volume).

| Data | About | Source | Purpose |
| --- | --- | --- | --- |
| Username | Learners, teachers | MindSpark (learners); entered by an admin (teachers) | Sign-in |
| Full name | Learners, teachers | MindSpark / admin | Shown to the learner and their teacher |
| Gender | Learners | MindSpark | Reports by gender (aggregate only) |
| Birth **year** (not date) | Learners | MindSpark date of birth | Age grouping, if needed |
| MindSpark UID (Kolibri "ID number") | Learners | MindSpark | Matching on re-import; never shown to learners |
| Password hash | Teachers, admins | Set in Kolibri | Sign-in. Learners have no password |
| Class and group memberships | Learners | MindSpark / teachers | Lessons and class reports |
| Roles | Teachers, admins | Admin | Access control |
| Activity logs: content opened, time spent, progress, quiz answers | Learners | Kolibri | Learner progress, teacher reports, monthly figures |
| Session logs: sign-in times, pages, browser and device type | All users | Kolibri | Monthly session figures |
| Monthly class record: Kolibri user ID, class name, gender, per reported month | Learners | The monthly report (`lshe_report.py`) | Keeps re-run reports identical. No names |

Not stored: learners' full dates of birth, MindSpark passwords, contact
details, parents' details or photos.

Other places that hold personal data:

- **Database backups** in `/srv/lshe-backups` on the centre server
  (owner-only permissions).
- **Kolibri's own server logs** in the Kolibri home volume. These can contain
  usernames and request details.
- **Exports** made at the end of the project (see below), until deleted.
- **The import log** (`/var/log/lshe/import.log`), only when an earlier run
  imported MindSpark *staff* accounts as learners: their usernames are
  listed so an admin can remove them. No learner names or usernames are
  logged.

These places don't hold personal data:

- **Monthly report files** (`/srv/lshe-reports`, and the copies on the
  provider's central machine). They are aggregate counts per class and
  gender, with no names, usernames, birth years or per-learner rows.
- **Import and report logs** in `/var/log/lshe`. Apart from the case above,
  they record counts only.

MindSpark is never written to. Its data stays under its own arrangements.

## Who can see it

| Who | Can see |
| --- | --- |
| A learner | Their own name, lessons and progress |
| A teacher (class coach) | Names and progress of learners in their own class only |
| A facility admin | All users and progress in the facility |
| The device superuser | Everything in Kolibri. For installers and support only |
| Server operators (shell or Docker access, over the VPN) | Everything, including the database and backups |
| The provider's central machine | Report files only, collected through a read-only account limited to `/srv/lshe-reports` |
| Anyone on the centre Wi-Fi who is not signed in | Nothing: no content and no user data |

Keep facility admin and superuser accounts to the people who need them, and
give teachers class coach accounts only. Signed-out users see no content,
and the adaptive assessment API is switched off. Before this deployment,
the assessment API was reachable without signing in. That was fixed by
requiring sign-in and class roles on every assessment endpoint.

## Retention

The retention periods below are proposals. UNESCO and the Ministry of
Education must agree them before learners use the system, and the agreed
values should replace these.

| Data | Proposed retention |
| --- | --- |
| Learner accounts and activity | The pilot, plus the agreed verification period after the final report, then deleted |
| Database backups | A rolling set (for example the last four weekly backups, plus the one before each import or upgrade); all deleted at the end |
| Kolibri server logs | Rotated by Kolibri; deleted with the server at the end |
| Monthly report files (aggregate) | May be kept as programme records |
| End-of-project exports | Only as long as the agreed handover requires, then deleted |

## End of project: export

Only export what the handover agreement requires. These files contain
personal data, so store them encrypted and delete them when no longer
needed. Run on each centre server:

```sh
K="docker exec lshe-kolibri kolibri manage"
$K bulkexportusers --facility <facility_id> --output-file /srv/lshe-backups/users.csv
$K exportlogs --log-type summary --output-file /srv/lshe-backups/summary_logs.csv
$K exportlogs --log-type session --output-file /srv/lshe-backups/session_logs.csv
```

The same exports are available to facility admins in the web interface
(**Facility → Data**).

## End of project: deletion

1. Make any agreed exports (above), and the final monthly report.
2. Delete the facility and everything in it:

   ```sh
   docker exec -it lshe-kolibri kolibri manage deletefacility --facility <facility_id>
   ```

   `deletefacility` doesn't cover two tables added by this fork for adaptive
   assessments (`ExamAssessment`, `ExamAssignmentAssessment`). Assessments
   are switched off on LSHE servers, so these tables should be empty. The
   fully reliable route is step 3.
3. Remove the server's data entirely:
   `cd docker/lshe && docker compose down -v`. This deletes the database and
   Kolibri home volumes.
4. Delete `/srv/lshe-backups`, any exports, and `docker/lshe/.env`. Use
   secure deletion, or wipe or destroy the disk, under the agreed
   procedure.
5. Record what was deleted, when and by whom, for the handover.

The aggregate report files may be kept (see Retention).
