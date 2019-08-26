# © 2004-2009 Tiny SPRL (<http://tiny.be>).
# © 2015 Agile Business Group <http://www.agilebg.com>
# © 2016 Grupo ESOC Ingeniería de Servicios, S.L.U. - Jairo Llopis
# © 2017 Tribunal Municipal de Cuentas de Rosario - Lisandro Gallo
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

{
    "name": "Automated Database Backups",
    "description": "Simplified version of 'auto_backup' module",
    "version": "10.0.2.0.0",
    "author": (
        "Yenthe Van Ginneken, "
        "Agile Business Group, "
        "Grupo ESOC Ingeniería de Servicios, "
        "LasLabs, "
        "Odoo Community Association (OCA)",
        "Tribunal Municipal de Cuentas de Rosario"
    ),
    'license': "AGPL-3",
    "website": "http://www.vanroey.be/applications/bedrijfsbeheer/odoo",
    "category": "Tools",
    "depends": [],
    "data": [
        "data/ir_cron.xml",
        "data/db_backup.xml",
        "view/db_backup.xml",
        "view/menu.xml"
    ],
    "application": True,
    "installable": True
}
