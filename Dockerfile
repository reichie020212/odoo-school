FROM odoo:19.0

USER root

# Custom addons — every school_* module ships in the production image.
COPY --chown=odoo:odoo school_academics  /mnt/extra-addons/odoo-school/school_academics
COPY --chown=odoo:odoo school_base       /mnt/extra-addons/odoo-school/school_base
COPY --chown=odoo:odoo school_canteen    /mnt/extra-addons/odoo-school/school_canteen
COPY --chown=odoo:odoo school_comms      /mnt/extra-addons/odoo-school/school_comms
COPY --chown=odoo:odoo school_exams      /mnt/extra-addons/odoo-school/school_exams
COPY --chown=odoo:odoo school_fees       /mnt/extra-addons/odoo-school/school_fees
COPY --chown=odoo:odoo school_homepage   /mnt/extra-addons/odoo-school/school_homepage
COPY --chown=odoo:odoo school_library    /mnt/extra-addons/odoo-school/school_library
COPY --chown=odoo:odoo school_portal     /mnt/extra-addons/odoo-school/school_portal
COPY --chown=odoo:odoo school_shop       /mnt/extra-addons/odoo-school/school_shop
COPY --chown=odoo:odoo school_transport  /mnt/extra-addons/odoo-school/school_transport

# Config
COPY --chown=odoo:odoo odoo.conf         /etc/odoo/odoo.conf

USER odoo
