{
    "name": "Classic Form Save/Discard Buttons",
    "version": "19.0.1.0.0",
    "summary": "Replace the form save indicator with labeled Save/Discard buttons",
    "author": "Tribunal Municipal de Cuentas - Municipalidad de Rosario",
    "website": "https://www.tmcrosario.gob.ar",
    "license": "AGPL-3",
    "category": "Technical",
    "depends": ["web"],
    "assets": {
        "web.assets_backend": [
            "web_classic_form_buttons/static/src/form_status_indicator/form_status_indicator.xml",
            "web_classic_form_buttons/static/src/form_controller/form_controller_patch.esm.js",
            "web_classic_form_buttons/static/src/control_panel/control_panel.scss",
        ],
    },
    "installable": True,
}
