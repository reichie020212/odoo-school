FROM odoo:19.0

USER root

# Custom addons (populate as modules are added)
# COPY --chown=odoo:odoo <module_name> /mnt/extra-addons/odoo-school/<module_name>

# Config
COPY --chown=odoo:odoo odoo.conf            /etc/odoo/odoo.conf

USER odoo
