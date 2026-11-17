# LSHE pilot: technical handover

Documentation for running Kolibri as the offline content server for the Life
Skills and Health Education (LSHE) pilot, Grades 4–7. It is written for
any capable provider taking over or replicating the deployment.

- [deployment.md](deployment.md): hardware, network, installation,
  provisioning, channels, grade bands, teachers, backup, restore and
  rollback, known limitations
- [roster-import.md](roster-import.md): importing learners and classes from
  MindSpark
- [reporting.md](reporting.md): monthly metrics, schedule, collection and
  combining
- [data-protection.md](data-protection.md): personal data stored, access,
  retention, export and deletion
- [acceptance-checklist.md](acceptance-checklist.md): checks to sign off
  before learners use a server

The Docker set-up is in [`docker/lshe/`](../../docker/lshe/). The scripts
that run a centre (roster import, channel import, grade bands, the monthly
report and central collection) are in the separate **kolibri_helper_scripts**
repository, in `lshe/`. On a centre server it is checked out at
`/opt/lshe/kolibri_helper_scripts`, and mounted read-only into the Kolibri
container. Commands in these pages that start with `lshe/` are in that
repository.
