"""
Set the channels allowed for a grade band (replacing any earlier list).

    kolibri manage setbandchannels --band G4-5 <channel_id> [<channel_id> ...]
    kolibri manage setbandchannels --band G4-5 --clear
    kolibri manage setbandchannels --list

Teacher channels (LSHE_TEACHER_CHANNEL_IDS) are refused: content in a band
can be assigned to learners, and teacher channels must never reach learners.
"""
import re

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction

from kolibri.core.content.models import ChannelMetadata
from kolibri.plugins.edulution.lshe_settings import normalise_channel_id
from kolibri.plugins.edulution.lshe_settings import teacher_channel_ids
from kolibri.plugins.edulution.models import BAND_NAME_MAX
from kolibri.plugins.edulution.models import ClassroomBand
from kolibri.plugins.edulution.models import GradeBandChannel

BAND_RE = re.compile(r"^[A-Za-z0-9_-]{1,%d}$" % BAND_NAME_MAX)


def validate_band(band):
    if not band or not BAND_RE.match(band):
        raise CommandError(
            "--band may only contain letters, digits, '-' and '_' (max {})".format(
                BAND_NAME_MAX
            )
        )
    return band


def print_bands(stdout):
    names = dict(ChannelMetadata.objects.values_list("id", "name"))
    bands = sorted(
        set(GradeBandChannel.objects.values_list("band", flat=True))
        | set(ClassroomBand.objects.values_list("band", flat=True))
    )
    if not bands:
        stdout.write("No grade bands set up yet.")
    for band in bands:
        stdout.write("{}".format(band))
        channels = GradeBandChannel.objects.filter(band=band).order_by("channel_id")
        for channel_id in channels.values_list("channel_id", flat=True):
            stdout.write(
                "  channel {} {}".format(
                    channel_id, names.get(channel_id, "(not imported on this server)")
                )
            )
        if not channels.exists():
            stdout.write("  no channels: nothing can be assigned to its classes")
        classes = ClassroomBand.objects.filter(band=band).order_by("classroom__name")
        for name in classes.values_list("classroom__name", flat=True):
            stdout.write("  class   {}".format(name))


class Command(BaseCommand):
    help = "Set the channels allowed for an LSHE grade band."

    def add_arguments(self, parser):
        parser.add_argument("channel_ids", nargs="*", help="Channel ids for the band")
        parser.add_argument("--band", help="Band name, e.g. G4-5")
        parser.add_argument(
            "--clear", action="store_true", help="Remove all channels from the band"
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="Show every band, its channels and classes",
        )

    def handle(self, *args, **options):
        if options["list"]:
            print_bands(self.stdout)
            return
        band = validate_band(options["band"])
        if options["clear"] == bool(options["channel_ids"]):
            raise CommandError("Give channel ids, or --clear (not both)")

        try:
            channel_ids = sorted(
                {normalise_channel_id(c) for c in options["channel_ids"]}
            )
            teacher = set(teacher_channel_ids())
        except ValueError as e:
            raise CommandError("Invalid channel id: {}".format(e))
        refused = sorted(set(channel_ids) & teacher)
        if refused:
            raise CommandError(
                "Teacher channels cannot be in a grade band: {}".format(
                    ", ".join(refused)
                )
            )

        with transaction.atomic():
            GradeBandChannel.objects.filter(band=band).delete()
            GradeBandChannel.objects.bulk_create(
                GradeBandChannel(band=band, channel_id=c) for c in channel_ids
            )

        imported = set(ChannelMetadata.objects.values_list("id", flat=True))
        for channel_id in channel_ids:
            if channel_id not in imported:
                self.stdout.write(
                    self.style.WARNING(
                        "Channel {} is not imported on this server yet.".format(
                            channel_id
                        )
                    )
                )
        self.stdout.write(
            "Band {} now allows {} channel(s).".format(band, len(channel_ids))
        )
