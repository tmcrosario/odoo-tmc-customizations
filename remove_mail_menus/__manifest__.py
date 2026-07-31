{
    "name": "Remove 'mail' addon menus",
    "version": "19.0.1.0.0",
    "author": "TMC Rosario",
    "license": "AGPL-3",
    "category": "base",
    "depends": ["mail"],
    "data": ["data/ir_ui_menu.xml"],
    "assets": {
        "web.assets_backend": [
            "remove_mail_menus/static/src/js/remove_mail_menus.js",
            "remove_mail_menus/static/src/scss/remove_mail_menus.scss",
        ],
    },
    "installable": True,
}
