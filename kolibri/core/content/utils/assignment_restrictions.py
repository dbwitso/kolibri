"""
Checks that content assigned in a lesson or quiz is allowed for every
classroom it reaches, and limits what a restricted learner can see, using
whatever ContentAssignmentRestrictionHook implementations are registered
(the edulution plugin's grade bands, for the LSHE deployment).

With no registered hook, nothing here restricts anything.
"""
from rest_framework.exceptions import ValidationError

from kolibri.core import error_constants
from kolibri.core.auth.constants import collection_kinds
from kolibri.core.content.hooks import ContentAssignmentRestrictionHook
from kolibri.core.content.models import ContentNode

MAX_TITLES_IN_MESSAGE = 5


def _hooks():
    return list(ContentAssignmentRestrictionHook.registered_hooks)


def _classroom_of(collection):
    """The classroom a collection belongs to, or None for a facility."""
    if collection.kind == collection_kinds.CLASSROOM:
        return collection
    if collection.kind in (
        collection_kinds.LEARNERGROUP,
        collection_kinds.ADHOCLEARNERSGROUP,
    ):
        return collection.parent
    return None


def _error(message):
    return ValidationError(message, code=error_constants.GRADE_BAND_NOT_ALLOWED)


def _titles(nodes):
    titles = sorted('"{}"'.format(title) for title in nodes)
    extra = len(titles) - MAX_TITLES_IN_MESSAGE
    shown = ", ".join(titles[:MAX_TITLES_IN_MESSAGE])
    return shown + (" and {} more".format(extra) if extra > 0 else "")


def _nodes(contentnode_ids):
    """{id: (channel_id, title)}; every id must exist on this server."""
    ids = {str(i).replace("-", "") for i in contentnode_ids if i}
    nodes = {
        node_id: (channel_id, title)
        for node_id, channel_id, title in ContentNode.objects.filter(
            id__in=ids
        ).values_list("id", "channel_id", "title")
    }
    if set(nodes) != ids:
        raise _error(
            "Some of this content is not on this server, so it cannot be assigned."
        )
    return nodes


def _targets(collections):
    """
    The classrooms the collections belong to, deduplicated and sorted by
    name. A facility-level collection is returned as itself.
    """
    targets = {}
    for collection in collections:
        if collection is None:
            continue
        target = _classroom_of(collection) or collection
        targets[target.id] = target
    return sorted(targets.values(), key=lambda c: c.name)


def _check_restriction(classroom, restriction, nodes):
    if restriction.label is None:
        raise _error(
            'Class "{}" has no grade band yet, so nothing can be '
            "assigned to it. Ask an administrator to set one.".format(classroom.name)
        )
    allowed = set(restriction.channel_ids)
    not_allowed = [
        title for channel_id, title in nodes.values() if channel_id not in allowed
    ]
    if not_allowed:
        raise _error(
            'Not allowed for class "{}" (grade band {}): {}. Only content '
            "from this band's channels can be assigned.".format(
                classroom.name, restriction.label, _titles(not_allowed)
            )
        )


def check_assignable(collections, contentnode_ids):
    """
    Raise a ValidationError (code GRADE_BAND_NOT_ALLOWED) unless every content
    node is allowed for every classroom that `collections` belong to.

    Nothing is checked, and nothing refused, for classrooms that no hook
    restricts.

    :param collections: Collection objects the lesson/quiz belongs or is
        assigned to (classroom, learner groups, ad hoc groups).
    :param contentnode_ids: ids of the resources (lessons) or exercises
        (quizzes).
    """
    hooks = _hooks()
    if not hooks or not any(contentnode_ids):
        return
    checks = []
    for target in _targets(collections):
        restrictions = [
            r
            for r in (hook.restriction_for_classroom(target) for hook in hooks)
            if r is not None
        ]
        if restrictions:
            checks.append((target, restrictions))
    if not checks:
        return
    nodes = _nodes(contentnode_ids)
    for target, restrictions in checks:
        if target.kind != collection_kinds.CLASSROOM:
            raise _error(
                "Content can only be assigned to a class or a group in a class, "
                "not to the whole facility."
            )
        for restriction in restrictions:
            _check_restriction(target, restriction, nodes)


def allowed_channel_ids_for_user(user):
    """
    None if no hook restricts `user`, otherwise the set of channel ids the
    user may see (the intersection over all hooks).
    """
    allowed = None
    for hook in _hooks():
        channel_ids = hook.allowed_channel_ids_for_user(user)
        if channel_ids is None:
            continue
        channel_ids = set(channel_ids)
        allowed = channel_ids if allowed is None else allowed & channel_ids
    return allowed
