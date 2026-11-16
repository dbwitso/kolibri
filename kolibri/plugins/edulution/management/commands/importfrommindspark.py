"""
Import MindSpark learners (and their classes) into a Kolibri facility over a
live MongoDB connection. No CSV step.

    kolibri manage importfrommindspark --facility <FACILITY_ID> --dryrun
    kolibri manage importfrommindspark --facility <FACILITY_ID>

The Mongo URI is read from $MINDSPARK_MONGO_URI (preferred, keeps the
password out of shell history and `ps`) or --mongo-uri.

Design notes
- Every write goes through Kolibri's ORM, so model validation and Kolibri's
  own bookkeeping run. Never write MindSpark data straight into Postgres.
- MindSpark is only read (find/ping). Nothing is ever written back to it.
- Learners are matched on MindSpark UID, stored in FacilityUser.id_number, so
  re-runs update in place instead of duplicating.
- MindSpark is the source of truth. By default the run is additive: learners
  deactivated in MindSpark are reported, not deleted. Pass --remove-inactive
  to also remove them from their Kolibri classes (end of term).
- MindSpark usernames are kept as they are, dots included (e.g.
  "kalonda.kamona"); this fork's Kolibri allows letters, digits, underscores
  and dots, max 30. Any other character becomes "_".
- Passwords are not ported (MindSpark stores MD5). Use a facility with
  learner_can_login_with_no_password (the "formal" preset).
- Class and role come from the learner's MindSpark product: the UserProducts
  document whose UPID is UserDetails.products.Mindspark.UPID.
  batch.ActiveBatch.grade/section give the class ("Grade 7 A"), and
  category ("student" or "teacher") the role. Only "student" accounts are
  imported, unless --staff-pattern is given, which then decides instead.

Requires pymongo in the Kolibri image.
"""
import os
import re
from collections import Counter

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction

from kolibri.core.auth.constants.demographics import FEMALE
from kolibri.core.auth.constants.demographics import MALE
from kolibri.core.auth.constants.demographics import NOT_SPECIFIED
from kolibri.core.auth.models import Classroom
from kolibri.core.auth.models import Facility
from kolibri.core.auth.models import FacilityUser
from kolibri.core.auth.models import Membership

try:
    from pymongo import MongoClient
except ImportError:  # pragma: no cover
    MongoClient = None


GENDER_MAP = {
    "boy": MALE,
    "girl": FEMALE,
    "m": MALE,
    "male": MALE,
    "f": FEMALE,
    "female": FEMALE,
}

# UserProducts.category of accounts that are imported as learners.
LEARNER_CATEGORY = "student"

USERNAME_MAX = 30
FULL_NAME_MAX = 120
CLASS_NAME_MAX = 100


class DryRunRollback(Exception):
    pass


def map_gender(value):
    return GENDER_MAP.get((value or "").strip().lower(), NOT_SPECIFIED)


def birth_year(dob):
    """MindSpark dateOfBirth 'YYYY-MM-DD' -> Kolibri 4-digit year, or NOT_SPECIFIED."""
    year = str(dob or "")[:4]
    if year.isdigit() and 1900 < int(year) < 2100:
        return year
    return NOT_SPECIFIED


def kolibri_username(ms_username):
    """Make a MindSpark username valid for Kolibri: [A-Za-z0-9_.], max 30.

    Dots are kept so learners sign in with their exact MindSpark username.
    """
    cleaned = re.sub(r"[^A-Za-z0-9_.]", "_", (ms_username or "").strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned[:USERNAME_MAX]


def full_name(details):
    name = (details.get("name") or "").strip()
    if not name:
        parts = [details.get("firstName") or "", details.get("lastName") or ""]
        name = " ".join(p.strip() for p in parts if p and p.strip())
    return name[:FULL_NAME_MAX]


def _mindspark_upids(um_db):
    """{UID: UPID of the learner's MindSpark product} from UserDetails."""
    upids = {}
    for d in um_db.UserDetails.find({}, {"UID": 1, "products.Mindspark.UPID": 1}):
        upid = ((d.get("products") or {}).get("Mindspark") or {}).get("UPID")
        if d.get("UID") and upid:
            upids[str(d["UID"])] = str(upid)
    return upids


def mindspark_products(um_db):
    """
    {UID: that learner's MindSpark UserProducts document}.

    A user can hold several products; the one whose UPID matches
    UserDetails.products.Mindspark.UPID is used. Without that link, the
    first product found is used.
    """
    upids = _mindspark_upids(um_db)
    products = {}
    fields = {"UID": 1, "UPID": 1, "category": 1, "batch.ActiveBatch": 1}
    for product in um_db.UserProducts.find({}, fields):
        uid = str(product.get("UID") or "")
        if not uid:
            continue
        upid = str(product.get("UPID") or product.get("_id") or "")
        wanted = upids.get(uid)
        if wanted is not None and upid != wanted:
            continue
        if wanted is None and uid in products:
            continue
        products[uid] = product
    return products


def class_name_for(product):
    """'Grade <grade> <section>' from batch.ActiveBatch, or None."""
    batch = (product.get("batch") or {}).get("ActiveBatch") or {}
    grade = str(batch.get("grade") or "").strip()
    section = str(batch.get("section") or "").strip()
    if not grade:
        return None
    name = "Grade {} {}".format(grade, section) if section else "Grade {}".format(grade)
    return name[:CLASS_NAME_MAX]


def build_class_map(um_db, products=None):
    """Return {mindspark_UID: kolibri_class_name}, e.g. "Grade 7 A"."""
    if products is None:
        products = mindspark_products(um_db)
    names = {uid: class_name_for(p) for uid, p in products.items()}
    return {uid: name for uid, name in names.items() if name}


def build_role_map(um_db, products=None):
    """Return {mindspark_UID: UserProducts.category}, e.g. "student"."""
    if products is None:
        products = mindspark_products(um_db)
    return {
        uid: str(p.get("category") or "").strip().lower() for uid, p in products.items()
    }


class Command(BaseCommand):
    help = "Import learners and classes from MindSpark MongoDB into a Kolibri facility."

    def add_arguments(self, parser):
        parser.add_argument(
            "--mongo-uri",
            default=None,
            help="MindSpark Mongo URI (default: $MINDSPARK_MONGO_URI)",
        )
        parser.add_argument(
            "--facility",
            default=None,
            help="Kolibri facility id (default: the device's default facility)",
        )
        parser.add_argument("--um-db", default="UserManagement")
        parser.add_argument("--auth-db", default="UserAuthentication")
        parser.add_argument(
            "--org-id",
            default=None,
            help="Only import learners with this MindSpark orgID",
        )
        parser.add_argument(
            "--staff-pattern",
            default=None,
            help=(
                "Regex on MindSpark username for accounts to skip. When given, it "
                "replaces the default rule (import only UserProducts.category "
                "'student')."
            ),
        )
        parser.add_argument(
            "--remove-inactive",
            action="store_true",
            help="Remove MindSpark-deactivated learners from their Kolibri classes",
        )
        parser.add_argument(
            "--dryrun",
            action="store_true",
            help="Do everything, report, then roll back",
        )

    # ---------------------------------------------------------------- helpers

    def get_facility(self, facility_id):
        if facility_id:
            try:
                return Facility.objects.get(pk=facility_id)
            except (Facility.DoesNotExist, ValueError):
                raise CommandError("Facility {} not found".format(facility_id))
        facility = Facility.get_default_facility()
        if not facility:
            raise CommandError("No default facility; pass --facility")
        return facility

    def unique_username(self, facility, wanted, uid, taken):
        """Avoid collisions with other users (not the one keyed on this UID)."""
        candidate, n = wanted, 1
        while (
            candidate in taken
            or FacilityUser.objects.filter(
                facility=facility, username__iexact=candidate
            )
            .exclude(id_number=uid)
            .exists()
        ):
            n += 1
            suffix = "_{}".format(n)
            candidate = wanted[: USERNAME_MAX - len(suffix)] + suffix
        return candidate

    def get_classroom(self, facility, name, cache):
        name = name[:CLASS_NAME_MAX]
        if name not in cache:
            classroom = Classroom.objects.filter(parent=facility, name=name).first()
            if classroom is None:
                classroom = Classroom.objects.create(parent=facility, name=name)
                self.stats["classes_created"] += 1
            cache[name] = classroom
        return cache[name]

    def set_class(self, facility, user, class_name, cache):
        """Put user in exactly one classroom: class_name (or none)."""
        current = Membership.objects.filter(user=user, collection__kind="classroom")
        target = self.get_classroom(facility, class_name, cache) if class_name else None
        for membership in current:
            if target is None or membership.collection_id != target.id:
                membership.delete()
                self.stats["class_removed"] += 1
        if target is not None and not current.filter(collection=target).exists():
            target.add_member(user)
            self.stats["class_added"] += 1

    def warn_if_passwords_required(self, facility):
        if not facility.dataset.learner_can_login_with_no_password:
            self.stdout.write(
                self.style.WARNING(
                    "Facility '{}' requires passwords. Imported learners get no usable "
                    "password; switch the facility to passwordless (formal preset) or "
                    "they will not be able to sign in.".format(facility.name)
                )
            )

    def connect(self, uri):
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        try:
            client.admin.command("ping")
        except Exception as e:
            raise CommandError("Cannot reach MindSpark Mongo: {}".format(e))
        return client

    def load_usernames(self, auth):
        """{UID (as a string): MindSpark username} from UserAuthentication."""
        return {
            str(d["UID"]): d.get("username")
            for d in auth.Authentication.find({}, {"UID": 1, "username": 1})
            if d.get("UID")
        }

    def resolve_username(self, facility, wanted, uid, existing, ms_username, taken):
        if existing and existing.username == wanted:
            username = wanted
        else:
            username = self.unique_username(facility, wanted, uid, taken)
        if username != ms_username:
            self.stats["username_changed"] += 1
        taken.add(username)
        return username

    def upsert_user(self, facility, uid, fields, existing):
        if existing:
            changed = [k for k, v in fields.items() if getattr(existing, k) != v]
            if changed:
                for k in changed:
                    setattr(existing, k, fields[k])
                existing.full_clean()
                existing.save()
                self.stats["updated"] += 1
            else:
                self.stats["unchanged"] += 1
            return existing
        # Same as FacilityUserModelManager.create_user with no password:
        # the literal NOT_SPECIFIED marks a passwordless account.
        user = FacilityUser(
            facility=facility, id_number=uid, password=NOT_SPECIFIED, **fields
        )
        user.full_clean()
        user.save()
        self.stats["created"] += 1
        return user

    # ------------------------------------------------------------------- main

    def handle(self, *args, **options):
        if MongoClient is None:
            raise CommandError("pymongo is not installed in this Kolibri environment")

        uri = options["mongo_uri"] or os.environ.get("MINDSPARK_MONGO_URI")
        if not uri:
            raise CommandError("Set $MINDSPARK_MONGO_URI or pass --mongo-uri")

        facility = self.get_facility(options["facility"])
        self.warn_if_passwords_required(facility)

        client = self.connect(uri)
        um = client[options["um_db"]]
        auth = client[options["auth_db"]]
        staff_re = (
            re.compile(options["staff_pattern"], re.I)
            if options["staff_pattern"]
            else None
        )

        usernames = self.load_usernames(auth)
        products = mindspark_products(um)
        class_map = build_class_map(um, products)
        self.roles = build_role_map(um, products)
        self.staff_re = staff_re
        self.staff_already_imported = []
        if not class_map:
            self.stdout.write(
                self.style.WARNING(
                    "No classes found in MindSpark (UserProducts.batch.ActiveBatch): "
                    "learners will be imported without classes and existing class "
                    "memberships left alone."
                )
            )

        query = {}
        if options["org_id"]:
            query["orgID"] = options["org_id"]

        self.stats = Counter()
        cache = {}
        taken = set()

        try:
            with transaction.atomic():
                for d in um.UserDetails.find(query):
                    self.import_one(
                        facility,
                        d,
                        usernames,
                        class_map,
                        options["remove_inactive"],
                        cache,
                        taken,
                    )
                if options["dryrun"]:
                    raise DryRunRollback()
        except DryRunRollback:
            self.stdout.write(self.style.NOTICE("Dry run: all changes rolled back."))
        finally:
            client.close()

        for key in sorted(self.stats):
            self.stdout.write("{:<28} {}".format(key, self.stats[key]))
        self.report_staff_already_imported()

    def report_staff_already_imported(self):
        if not self.staff_already_imported:
            return
        self.stdout.write(
            self.style.WARNING(
                "These Kolibri accounts are staff in MindSpark but were imported "
                "earlier as learners. The import leaves them alone; remove them in "
                "Facility > Users, or make them coaches:"
            )
        )
        for username in sorted(self.staff_already_imported):
            self.stdout.write("  {}".format(username))

    def is_staff(self, uid, ms_username):
        """
        Whether to skip this account as staff. --staff-pattern decides when
        given; otherwise only MindSpark "student" products are learners.
        Returns None when the account has no MindSpark product at all.
        """
        if self.staff_re is not None:
            return bool(self.staff_re.search(ms_username))
        role = self.roles.get(uid)
        if role is None:
            return None
        return role != LEARNER_CATEGORY

    def import_one(
        self, facility, d, usernames, class_map, remove_inactive, cache, taken
    ):
        # UID may be stored as an ObjectId or a number; id_number is a string.
        uid = d.get("UID") or d.get("_id")
        uid = str(uid) if uid else None
        ms_username = usernames.get(uid)
        if not uid or not ms_username:
            self.stats["skipped_no_username"] += 1
            return
        existing = FacilityUser.objects.filter(facility=facility, id_number=uid).first()

        staff = self.is_staff(uid, ms_username)
        if staff is None:
            self.stats["skipped_no_mindspark_product"] += 1
            return
        if staff:
            self.stats["skipped_staff"] += 1
            if existing:
                self.staff_already_imported.append(existing.username)
            return

        if d.get("status") != "A":
            self.stats["inactive_in_mindspark"] += 1
            if existing and remove_inactive:
                self.set_class(facility, existing, None, cache)
                self.stats["inactive_removed_from_class"] += 1
            return

        wanted = kolibri_username(ms_username)
        if not wanted:
            self.stats["skipped_bad_username"] += 1
            return
        fields = {
            "username": self.resolve_username(
                facility, wanted, uid, existing, ms_username, taken
            ),
            "full_name": full_name(d),
            "gender": map_gender(d.get("gender")),
            "birth_year": birth_year(d.get("dateOfBirth")),
        }

        user = self.upsert_user(facility, uid, fields, existing)

        if class_map:
            class_name = class_map.get(uid)
            if class_name:
                self.set_class(facility, user, class_name, cache)
            else:
                self.stats["no_class_in_mindspark"] += 1
