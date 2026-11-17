# Roster import from MindSpark

Learners and classes on an LSHE centre server come from that centre's
MindSpark roster. MindSpark is the numeracy platform that already holds
the centre's learners, in MongoDB. The import only ever **reads** MindSpark.
Nothing is written back, and no report is linked to MindSpark.

## How the import works

`import_from_mindspark.py` (kolibri_helper_scripts, `lshe/`) runs inside the
Kolibri container. It connects to MindSpark's MongoDB and:

1. Reads learners from `UserManagement.UserDetails` (name, gender, date of
   birth, status, organisation) and their usernames from
   `UserAuthentication.Authentication`, matched on the MindSpark `UID`.
2. Finds each user's MindSpark product: the `UserManagement.UserProducts`
   record whose `UPID` matches `UserDetails.products.Mindspark.UPID`. Its
   `category` is the user's role, and its `batch.ActiveBatch` is their
   current class (grade and section).
3. Imports only accounts whose role is `student`. Teacher and other staff
   accounts are skipped, whatever their username, as are accounts with no
   username or no MindSpark product. `--staff-pattern` replaces the role rule
   with a username pattern, as an override.
4. For each active learner (status `A`), creates or updates a Kolibri learner
   in the facility:
   - **Matched on MindSpark UID**, which is stored in the learner's Kolibri
     "ID number" field. Re-running updates learners in place, never
     duplicating them, even if a name or username changes.
   - **Username:** the exact MindSpark username, dots included (for example
     `kalonda.kamona`). Characters other than letters, digits, `_` and `.`
     become `_`, and usernames are cut to 30 characters. If another Kolibri
     account already has the username, the learner gets a suffix
     (`kalonda.kamona_2`), and the run reports it.
   - **Gender:** boy/girl/M/F become male/female; anything else is "not
     specified".
   - **Birth year only**, taken from the date of birth. The full date is not
     stored.
   - **No password.** MindSpark passwords are not copied. Learners sign in by
     username alone (formal preset).
5. Puts each learner in their current MindSpark class, creating Kolibri
   classes as needed with consistent names: `Grade <grade> <section>`, for
   example `Grade 7 A`. A learner who moved class in MindSpark is moved in
   Kolibri, and leaves the old class's groups. A learner with no current
   class in MindSpark keeps their Kolibri classes unchanged.
6. Writes everything through Kolibri's own data layer, never with SQL, and
   in one transaction: a failed run changes nothing.

A learner who is deactivated in MindSpark (status `D`) is reported but left
in their class, unless `--remove-inactive` is given. In that case they are
taken out of all their classes. Their Kolibri account and activity history
are never deleted by the import.

If a MindSpark staff account was imported as a learner by an earlier run
(before roles were read from MindSpark), the import lists it at the end of
its output. It never deletes accounts: remove them in **Facility → Users**,
or make them coaches.

## When to run it

| When | What | Command |
| --- | --- | --- |
| Before learners first use the server | Create every learner | `run_import.sh --apply` |
| Start of each term | Add new learners and pick up name changes | `run_import.sh --apply` |
| End of each term | Take out learners who have left and apply class changes | `run_import.sh --apply --remove-inactive` |
| Any time | See what would change | `run_import.sh` (dry run only) |

Leave removals and class moves to the end of term. Moving a learner between
classes mid-term changes which lessons they see and which class their
activity counts towards in reports.

After an import that creates classes, set the new classes' grade bands
(`set_class_band.py`, see [deployment.md](deployment.md)). A class with no band
can't be given any lessons.

## Running it

Use the wrapper on the centre server, from
`/opt/lshe/kolibri_helper_scripts/lshe/`, as root:

```sh
./run_import.sh --org-id <ORG>            # dry run: shows the counts, changes nothing
./run_import.sh --apply --org-id <ORG>    # dry run, database backup, then import
```

With `--apply`, the wrapper backs up the Kolibri database first (and checks
the backup can be read), then runs the import. If the import fails, nothing
is written. To undo a successful import, restore the backup (see
[deployment.md](deployment.md)).

The counts printed at the end include `created`, `updated`, `unchanged`,
`skipped_staff`, `skipped_no_username`, `skipped_no_mindspark_product`,
`username_changed`,
`inactive_in_mindspark`, `inactive_removed_from_class`, `classes_created`,
`class_added`, `class_removed` and `no_class_in_mindspark`. Check them on
every dry run before applying. A large `created` count on a centre that is
already set up usually means the wrong `--org-id`.

## Options

| Option | Default | Meaning |
| --- | --- | --- |
| `--mongo-uri` | `$MINDSPARK_MONGO_URI` | MindSpark MongoDB address. Prefer the environment variable, which keeps the password out of shell history |
| `--facility` | the device's default facility | Kolibri facility ID |
| `--org-id` | all | Only import learners with this MindSpark `orgID` |
| `--staff-pattern` | none (use MindSpark roles) | Regular expression on the MindSpark username. When given, matching accounts are skipped and MindSpark roles are ignored. Use only if the role data is wrong |
| `--remove-inactive` | off | Take MindSpark-deactivated learners out of their Kolibri classes |
| `--dryrun` | off | Do everything, report, then roll back |
| `--um-db`, `--auth-db` | `UserManagement`, `UserAuthentication` | MindSpark database names |

## Requirements

- MindSpark's MongoDB must be reachable from the Kolibri container. Inside
  the container, `127.0.0.1` is the container, not the host. See
  `docker/lshe/README.md` for `bindIp` and firewall settings.
- Use MindSpark's existing login in `MINDSPARK_MONGO_URI` (in
  `docker/lshe/.env`). The import only reads `UserManagement` and
  `UserAuthentication`. Don't create or change MindSpark users for it.
- The facility should use the formal preset. The import warns if learners
  would need a password.

Teachers aren't imported. Create them by hand as class coaches (see
[deployment.md](deployment.md)).
