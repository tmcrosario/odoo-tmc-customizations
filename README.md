# Odoo TMC Customizations

![Odoo 19.0](https://img.shields.io/badge/Odoo-19.0-714B67)
[![Licencia: AGPL-3](https://img.shields.io/badge/licencia-AGPL--3-blue.svg)](LICENSE)

Módulos complementarios de los addons del TMC.

## Módulos

| Módulo                                                  | Versión    | Descripción                                                                 |
| ------------------------------------------------------- | ---------- | --------------------------------------------------------------------------- |
| [`automated_backups`](automated_backups/)               | 19.0.1.0.0 | Copias de seguridad automáticas (versión simplificada de `auto_backup`)     |
| [`popup_message_dialog_box`](popup_message_dialog_box/) | 19.0.1.0.1 | Diálogo emergente de mensajes                                               |
| [`remove_mail_menus`](remove_mail_menus/)               | 19.0.1.0.0 | Oculta los menús de Actividades, Conversaciones y Discuss del módulo `mail` |
| [`remove_odoo_bindings`](remove_odoo_bindings/)         | 19.0.1.1.0 | Desactiva los vínculos con odoo.com del código estándar                     |
| [`web_classic_form_buttons`](web_classic_form_buttons/) | 19.0.1.0.0 | Botones Guardar/Descartar con etiqueta en el formulario                     |
| [`web_notification`](web_notification/)                 | 19.0.1.0.0 | Bandeja de notificaciones internas con campana en la barra superior         |

## Instalación

Dependencia de `web_notification`: [`odoo-tmc`](https://github.com/tmcrosario/odoo-tmc).

Agregar a la ruta de addons, actualizar aplicaciones e instalar los módulos necesarios.

## Licencia

[AGPL-3](LICENSE). Autores: ver el `__manifest__.py` de cada módulo.
