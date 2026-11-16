"""
Kolibri Content hooks
---------------------

Hooks for managing the display and rendering of content.
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import json
from abc import abstractmethod
from abc import abstractproperty
from collections import namedtuple

from django.utils.safestring import mark_safe

from kolibri.core.webpack.hooks import WebpackBundleHook
from kolibri.core.webpack.hooks import WebpackInclusionMixin
from kolibri.plugins.hooks import define_hook
from kolibri.plugins.hooks import KolibriHook


@define_hook
class ContentRendererHook(WebpackBundleHook, WebpackInclusionMixin):
    """
    An inheritable hook that allows special behaviour for a frontend module that defines
    a content renderer.
    """

    #: Set tuple of format presets that this content renderer can handle
    @abstractproperty
    def presets(self):
        pass

    @classmethod
    def html(cls):
        tags = []
        for hook in cls.registered_hooks:
            tags.append(hook.render_to_page_load_async_html())
        return mark_safe("\n".join(tags))

    def render_to_page_load_async_html(self):
        """
        Generates script tag containing Javascript to register a content renderer.

        :returns: HTML of a script tag to insert into a page.
        """
        # Note, while most plugins use sorted chunks to filter by text direction
        # content renderers do not, as they may need to have styling for a different
        # text direction than the interface due to the text direction of content
        urls = [chunk["url"] for chunk in self.bundle]
        tags = (
            self.frontend_message_tag()
            + self.plugin_data_tag()
            + [
                '<script>{kolibri_name}.registerContentRenderer("{bundle}", ["{urls}"], {presets});</script>'.format(
                    kolibri_name="kolibriCoreAppGlobal",
                    bundle=self.unique_id,
                    urls='","'.join(urls),
                    presets=json.dumps(self.presets),
                )
            ]
        )
        return mark_safe("\n".join(tags))


@define_hook
class ContentNodeDisplayHook(KolibriHook):
    """
    A hook that registers a capability of a plugin to provide a user interface
    for a content node. When subclassed, this hook should expose a method that
    accepts a ContentNode instance as an argument, and returns a URL where the
    interface to interacting with that node for the user is exposed.
    If this plugin cannot produce an interface for this particular content node
    then it may return None.
    """

    @abstractmethod
    def node_url(self, content_node):
        pass


#: What a ContentAssignmentRestrictionHook says about one classroom.
#: label: a name for the restriction to show coaches (e.g. a grade band), or
#:   None when the classroom has no restriction configured, which means
#:   nothing may be assigned to it.
#: channel_ids: the channel ids (hex) whose content may be assigned.
ChannelRestriction = namedtuple("ChannelRestriction", ["label", "channel_ids"])


@define_hook
class ContentAssignmentRestrictionHook(KolibriHook):
    """
    Limits which channels' content may be assigned to a classroom (lessons and
    quizzes), and which channels a restricted learner may see.

    Used by kolibri.core.content.utils.assignment_restrictions. When no hook
    is registered there is no restriction.
    """

    @abstractmethod
    def restriction_for_classroom(self, classroom):
        """
        :type classroom: kolibri.core.auth.models.Classroom
        :return: None if this hook does not restrict the classroom, otherwise
            a ChannelRestriction.
        """

    @abstractmethod
    def allowed_channel_ids_for_user(self, user):
        """
        :type user: kolibri.core.auth.models.FacilityUser
        :return: None if this hook does not restrict the user, otherwise the
            set of channel ids (hex) the user may see content from.
        """
