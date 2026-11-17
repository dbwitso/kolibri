# Acceptance checklist

Run these checks on each centre server, after installation and before
learners use it. Sign them off with UNESCO. Repeat the checks marked ★
after every upgrade.

Use a test class in each band (for example `Grade 4 A` in G4-5 and
`Grade 6 A` in G6-7), a test learner in each, and a test teacher assigned to
`Grade 4 A` only. Remove the test accounts afterwards, or keep them out of
the real classes so they don't appear in reports.

Record for each check: date, server (centre code), tester, result
(pass/fail), and evidence (screenshot, or command output).

## 1. Setup

| # | Check | How | Expected |
| --- | --- | --- | --- |
| 1.1 | Formal preset | Facility → Settings | Learners sign in with no password; learners cannot edit their account; guest access off |
| 1.2 | Bands set | `lshe/run_script.sh set_class_band.py --list` | Every class is in a band; every band lists its LSHE channels; no teacher channel in any band |
| 1.3 | Teacher channels configured | `.env` has `LSHE_TEACHER_CHANNEL_IDS` | The IDs of every teacher channel |
| 1.4 | Ports | From a tablet: `http://<server>:8080` and `http://<server>:<LSHE_ZIP_PORT>` (default 8081) | Both answer. The zip port shows an error page for the bare address; that is normal |
| 1.5 | No other exposure | From a device on another network (VPN): ports 8080, the zip port, 5432 | Not reachable |

## 2. Grade bands ★

| # | Check | How | Expected |
| --- | --- | --- | --- |
| 2.1 | In-band assignment works | As the teacher, create a lesson for `Grade 4 A` with a G4-5 video, and activate it | Saved |
| 2.2 | Out-of-band assignment refused | As a facility admin, try to add a G6-7 resource to a `Grade 4 A` lesson, or to create a quiz from G6-7 exercises | Refused, with a message naming the class, its band and the content |
| 2.3 | Class with no band refused | Create a class, don't set a band, try to assign any lesson | Refused: "has no grade band" |

## 3. A Grade 4 learner can't see Grade 6–7 content ★

Sign in on a tablet as the `Grade 4 A` test learner.

| # | Check | How | Expected |
| --- | --- | --- | --- |
| 3.1 | Through the UI | Browse Home, Library, search for a known G6-7 title | Only assigned G4-5 content; G6-7 titles never appear |
| 3.2 | Through the API | In the same browser, open `http://<server>:8080/api/content/contentnode/<G6-7 node id>/`, `/api/content/channel/`, `/api/content/contentnode_search/?search=<G6-7 title>`, `/api/content/file/` | Not found, or results without any G6-7 content or channel names |
| 3.3 | Public API off | Open `http://<server>:8080/api/public/v2/channel/` and `/api/public/v1/channels` | Not found |
| 3.4 | Signed out | Sign out, then repeat 3.2 | No content at all |
| 3.5 | Through direct URLs | As the learner, try to reach a G6-7 file by guessing or browsing URLs | No route gives the learner a G6-7 file address. **Known limitation:** a file URL obtained elsewhere (for example from a teacher's screen) does download. See [deployment.md](deployment.md), "Known limitations". UNESCO should explicitly accept this limitation |

## 4. Teachers ★

| # | Check | How | Expected |
| --- | --- | --- | --- |
| 4.1 | Own class only | Sign in as the test teacher, open Coach | Only `Grade 4 A` is listed; other classes' learners and reports cannot be opened |
| 4.2 | Not an admin | As the teacher, look for Facility in the menu | Not available |
| 4.3 | Teacher channel visible to teachers | As the teacher, browse the Library | The teacher channels (CSE course for teachers, ICT in Education, AI in Education) are listed and play |

## 5. Learners can't see the teacher channel ★

| # | Check | How | Expected |
| --- | --- | --- | --- |
| 5.1 | UI | As each test learner, browse and search for a teacher-channel title | Never shown |
| 5.2 | API | As a learner, then signed out: `/api/content/channel/`, `/api/content/contentnode/?channel_id=<teacher channel id>` | Teacher channels absent |
| 5.3 | Assignment | As an admin, try to assign teacher-channel content to a learner class | Refused |

## 6. Reporting

Use a test learner in a test class, and run the report for the current month
(partial reports are allowed and are not saved for later months):
`sudo lshe/run_monthly_report.sh <YYYY-MM>` (in kolibri_helper_scripts).

| # | Check | How | Expected |
| --- | --- | --- | --- |
| 6.1 | Completed video counts as reached | The learner watches one LSHE video to the end, then run the report | `reached_new` and `reached_cumulative` are 1 for that class and gender |
| 6.2 | Half-watched video doesn't | A second test learner watches half a video | Not reached; their time appears in `video_watch_seconds` |
| 6.3 | Teacher activity excluded | The test teacher completes a video | Figures unchanged |
| 6.4 | Teacher channel excluded | A coach completes teacher-channel content | Figures unchanged |
| 6.5 | No personal data | Open the CSV and JSON | No names, usernames, birth years or per-learner rows |
| 6.6 | Re-run is identical | Run the same month twice and compare the CSVs (`cmp`) | Identical |
| 6.7 | Collection | From the central machine, `collect_reports.sh` then `combine_reports.py --month <YYYY-MM>` | The centre's file is collected, and the centre is not listed as missing |

## 7. Playback on tablets ★

| # | Check | How | Expected |
| --- | --- | --- | --- |
| 7.1 | Video plays | On a tablet, as a learner, play an assigned LSHE video, then seek forwards and backwards | Plays smoothly; seeking works. Videos are served from port 8080 |
| 7.2 | HTML5 / H5P content opens | Open an assigned interactive (HTML5 or H5P) resource | It loads and responds. These are served from the zip port (`LSHE_ZIP_PORT`, default 8081); if it is blocked they stay blank |
| 7.3 | A full class streams at once | With the largest class's number of tablets, all learners start the same video within a minute and watch for 10 minutes | No tablet stalls for more than a few seconds; record the access point's peak throughput and the server's CPU load |

## 8. Operations

| # | Check | How | Expected |
| --- | --- | --- | --- |
| 8.1 | Roster dry run | `lshe/run_import.sh --org-id <ORG>` | Counts printed; nothing changed (learner count before and after is the same) |
| 8.2 | Backup and restore | Take a backup, restore it to a scratch database or a spare server | Restore succeeds; users and classes present |
| 8.3 | Report timer | `systemctl list-timers lshe-report.timer` | Next run on the 1st at 02:00 |
| 8.4 | Restart | Reboot the server | Kolibri is back without manual steps; learners can sign in |
