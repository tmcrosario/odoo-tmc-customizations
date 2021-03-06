{
    'name': 'Project Task Kanban Direct Link',
    'version': '13.0.1.0.0',
    'category': 'Project',
    'website': 'https://www.tmcrosario.gob.ar',
    'author': 'Tribunal Municipal de Cuentas - Municipalidad de Rosario',
    'license': 'AGPL-3',
    'sequence': 10,
    'summary': 'Projects, Tasks',
    'depends': [
        'project',
        'project_task_code'],
    'data': [
        'views/project_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}  # yapf: disable
