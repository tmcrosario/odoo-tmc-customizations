{
    "name": "Remove 'mail' addon menus",
    "version": "19.0.1.0.0",
    "author": "TMC Rosario",
    "license": "AGPL-3",
    "category": "base",
    "depends": ["mail"],
    "data": ["data/mail_channel_views.xml"],
    "assets": {
        "web.assets_backend": [
            "remove_mail_menus/static/src/js/systray.js",
        ],
    },
    "installable": True,
}
