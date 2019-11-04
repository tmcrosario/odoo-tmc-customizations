# 2004-2009 Tiny SPRL (<http://tiny.be>).
# 2015 Agile Business Group <http://www.agilebg.com>
# 2016 Grupo ESOC Ingenieria de Servicios, S.L.U. - Jairo Llopis
# 2017 Tribunal Municipal de Cuentas de Rosario - Lisandro Gallo
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

{
    "name": "Automated Database Backups",
    "version": "13.0.1.0.0",
    "author": "Yenthe Van Ginneken, Agile BG, ESOC, LasLabs, OCA, TMC Rosario",
    'license': "AGPL-3",
    "website": "http://www.vanroey.be/applications/bedrijfsbeheer/odoo",
    "category": "Tools",
    "depends": [],
    "data": [
        "data/db_backup_data.xml",
        "data/ir_cron_data.xml",
        "views/db_backup_views.xml",
        "views/automated_backups_menus.xml"
    ],
    "application": True,
    "installable": True
}  # yapf: disable
