"""
Set (or clear) the grade band of a classroom.

    kolibri manage setclassband --class "Grade 5 A" --band G4-5
    kolibri manage setclassband --class-id <classroom_id> --band G6-7
    kolibri manage setclassband --class "Grade 5 A" --clear
    kolibri manage setclassband --list

A class with no band can receive no lesson or quiz assignments. Changing a
band does not change lessons or quizzes already saved; learners simply stop
seeing content outside the new band's channels.
"""
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from kolibri.core.auth.models import Classroom
from kolibri.core.auth.models import Facility
from kolibri.plugins.edulution.management.commands.setbandchannels import print_bands
from kolibri.plugins.edulution.management.commands.setbandchannels import validate_band
from kolibri.plugins.edulution.models import ClassroomBand
from kolibri.plugins.edulution.models import GradeBandChannel


class Command(BaseCommand):
    help = "Set the LSHE grade band of a classroom."

    def add_arguments(self, parser):
        target = parser.add_mutually_exclusive_group()
        target.add_argument("--class", dest="class_name", help="Classroom name")
        target.add_argument("--class-id", help="Classroom id")
        parser.add_argument(
            "--facility", help="Facility id (default: the device's default facility)"
        )
        parser.add_argument("--band", help="Band name, e.g. G4-5")
        parser.add_argument(
            "--clear", action="store_true", help="Remove the class's band"
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="Show every band, its channels and classes",
        )

    def get_classroom(self, options):
        if options["class_id"]:
            classroom = Classroom.objects.filter(id=options["class_id"]).first()
            if classroom is None:
                raise CommandError("No class with id {}".format(options["class_id"]))
            return classroom
        if not options["class_name"]:
            raise CommandError("Give --class or --class-id")
        if options["facility"]:
            facility = Facility.objects.filter(id=options["facility"]).first()
        else:
            facility = Facility.get_default_facility()
        if facility is None:
            raise CommandError("Facility not found; pass --facility")
        matches = list(
            Classroom.objects.filter(parent=facility, name=options["class_name"])
        )
        if not matches:
            raise CommandError(
                'No class named "{}" in {}'.format(options["class_name"], facility.name)
            )
        if len(matches) > 1:
            raise CommandError(
                'Several classes are named "{}"; use --class-id ({})'.format(
                    options["class_name"], ", ".join(c.id for c in matches)
                )
            )
        return matches[0]

    def handle(self, *args, **options):
        if options["list"]:
            print_bands(self.stdout)
            return
        classroom = self.get_classroom(options)
        if options["clear"]:
            if options["band"]:
                raise CommandError("Give --band or --clear (not both)")
            ClassroomBand.objects.filter(classroom=classroom).delete()
            self.stdout.write(
                '"{}" has no band now: it can receive no assignments.'.format(
                    classroom.name
                )
            )
            return
        band = validate_band(options["band"])
        ClassroomBand.objects.update_or_create(
            classroom=classroom, defaults={"band": band}
        )
        self.stdout.write('"{}" is now in band {}.'.format(classroom.name, band))
        if not GradeBandChannel.objects.filter(band=band).exists():
            self.stdout.write(
                self.style.WARNING(
                    "Band {} has no channels yet; run setbandchannels.".format(band)
                )
            )
