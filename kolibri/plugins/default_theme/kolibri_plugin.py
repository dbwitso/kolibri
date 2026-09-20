from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import datetime
from django.templatetags.static import static
from kolibri.core import theme_hook
from kolibri.plugins import KolibriPluginBase
from kolibri.plugins.hooks import register_hook
import random


class DefaultThemePlugin(KolibriPluginBase):
    pass


@register_hook
class DefaultThemeHook(theme_hook.ThemeHook):
    @property
    def theme(self):
        # Get a random image of the 31 available images
        random_image = random.randint(1, 31)

        # Generate the background image filename based on the random number between 1 and 31
        background_image = static(
            "assets/default_theme/background{}.jpg".format(random_image)
        )

        return {
            "brandColors": {
                # Generated as a tint/shade ramp from the Edulution brand blue
                # (#035db8, set at v_400 - the shade the "primary" token maps to).
                "primary": {
                    "v_50": "#ebf2f9",
                    "v_100": "#cddff1",
                    "v_200": "#9abee3",
                    "v_300": "#5b96d1",
                    "v_400": "#035db8",
                    "v_500": "#0352a2",
                    "v_600": "#02478c",
                    "v_700": "#023c76",
                    "v_800": "#022e5c",
                    "v_900": "#012140",
                },
                "secondary": {
                    "v_50": "#e3f0ed",
                    "v_100": "#badbd2",
                    "v_200": "#8dc5b6",
                    "v_300": "#62af9a",
                    "v_400": "#479e86",
                    "v_500": "#368d74",
                    "v_600": "#328168",
                    "v_700": "#2c715a",
                    "v_800": "#26614d",
                    "v_900": "#1b4634",
                },
            },
            "signIn": {
                "background": background_image,
                "backgroundImgCredit": "Edulution",
                "topLogo": {
                    "src": static("assets/default_theme/edulution-logo.svg"),
                    "alt": "Edulution",
                    "style": "padding-left: 64px; padding-right: 64px; margin-bottom: 8px; margin-top: 8px",
                },
                "footerLogo": {
                    "src": static("assets/default_theme/edulution-symbol.png"),
                    "alt": "Edulution",
                    "style": "height: 24px; width: 24px",
                },
            },
            "sideNav": {
                "topLogo": {
                    "src": static("assets/default_theme/edulution-logo.svg"),
                    "alt": "Edulution",
                    "style": "padding: 8px 16px; margin-bottom: 8px; margin-top: 8px",
                },
                "showKolibriFooterLogo": False,
            },
            "logos": [
                {
                    "src": static("assets/default_theme/logo.ico"),
                    "content_type": "image/vnd.microsoft.icon",
                    "size": "32x32",
                },
                {
                    "src": static("assets/default_theme/kolibri-logo.svg"),
                    "content_type": "image/svg+xml",
                    "maskable": False,
                    "size": "any",
                },
                {
                    "src": static("assets/default_theme/kolibri-logo-192.png"),
                    "content_type": "image/png",
                    "size": "192x192",
                },
                {
                    "src": static("assets/default_theme/kolibri-logo-512.png"),
                    "content_type": "image/png",
                    "size": "512x512",
                },
            ],
        }
