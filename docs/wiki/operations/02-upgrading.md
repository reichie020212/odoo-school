---
title: Upgrading between Odoo versions
description: How to lift a school_* install from Odoo 19 to a future major
published: true
date: 2026-04-25
tags: operations, upgrade, migration
editor: markdown
---

# Upgrading between Odoo versions

The School Management System targets **Odoo 19.0** exclusively. Future majors (20.0+) will likely require changes to our modules — `_sql_constraints` patterns, RelaxNG schemas, and portal templates all evolve release to release.

## Staying on 19.0

Minor Odoo releases (19.0.1, 19.0.2, ...) ship via the Docker image tag `odoo:19.0`. You're already on it if your `docker-compose.yml` references `odoo:19.0`. To pick up a minor:

```bash
docker compose pull odoo
docker compose up -d odoo
```

The running container restarts onto the newer image. No DB migration needed for minors; Odoo auto-updates the schema on boot if the release included schema tweaks.

## Upgrading to Odoo 20.0 (future)

Don't do this blindly. The upgrade checklist:

### 1. Read the release notes

Odoo publishes breaking changes at <https://www.odoo.com/documentation/20.0/>. Scan for:

- Field renames on models we inherit (`res.partner`, `hr.employee`, `account.move`, `product.template`, `stock.picking`, `calendar.event`, `mail.template`, `base.automation`).
- Changes to portal templates.
- Deprecated API calls.
- Changes to the RelaxNG schema for view XML.

Our [Odoo 19 specifics doc](../reference/odoo-19-specifics.md) lists every Odoo 19 pattern we rely on. Check each against the 20.0 docs.

### 2. Stand up an upgrade DB

```bash
# Backup prod first (see backup-and-restore doc)
DB_UPGRADE=school_upgrade_test
cp $BACKUP/school_prod.dump /tmp/
# ... restore into DB_UPGRADE ...

# Bump to 20 image
sed -i.bak 's/odoo:19.0/odoo:20.0/g' docker-compose.yml
docker compose pull odoo

# Run upgrade
docker compose run --rm --no-deps odoo odoo \
    -d "$DB_UPGRADE" -u all --stop-after-init
```

`-u all` runs migrations for every installed module. Odoo writes upgrade logs to the container's stdout — capture them and grep for `ERROR` / `WARNING`.

### 3. Update our modules

Expect each `school_*` module to need edits. Typical surface:

- `__manifest__.py` — bump `version` to `20.0.x.y.z`.
- Models — check that every `_inherit` target still exists with the same field names. Rename anywhere Odoo renamed.
- Views — re-validate against the new RelaxNG schema. `<list>` / `<tree>` / decoration attrs may have changed.
- Security — `res.groups.privilege` might be restructured again. Check.
- Mail templates — retest `t-out` / `{{ }}` rendering.
- Automation — `base.automation` trigger types evolve.

Run each module's test suite as you go:

```bash
docker compose run --rm --no-deps odoo odoo \
    -d "$DB_UPGRADE" -u school_base --test-enable \
    --test-tags=/school_base --stop-after-init
```

Repeat for every school module.

### 4. Regression test the app

Spot-check each major flow on the upgraded DB:

- [ ] New student creation → admission number auto-generated.
- [ ] Course Session generation → calendar events created.
- [ ] Exam result entry → percentage / letter grade / GPA computed.
- [ ] Report card Generate Course Lines → lines populated with correct weighted avg.
- [ ] Fee enrollment Generate Invoice → invoice created with scholarship line.
- [ ] Library loan Confirm Borrow → copy flips to borrowed.
- [ ] Canteen wallet Post top-up → balance increases.
- [ ] Shop sale Confirm → stock.picking created.
- [ ] Transport Assignment activate → DB constraint enforces one active per year.
- [ ] Portal `/my/school` → shows correct data for a guardian portal user.
- [ ] Homepage `/` → stats display correctly.

### 5. Promote

Only when the upgrade DB passes all regression tests:

1. Schedule a maintenance window (typically 30–60 min for a small school).
2. Put up a static maintenance page.
3. Backup prod one last time.
4. Stop Odoo. Restore the upgrade DB over prod (or rename `school_prod` → `school_prod_old` and the upgraded one to `school_prod`).
5. Bump `docker-compose.yml` to the new image tag.
6. Start Odoo. Run a quick smoke test.
7. Take the maintenance page down.
8. Keep `school_prod_old` for ~30 days in case you need to roll back.

### 6. Deprecate the old DB

Once you're confident in the upgraded DB (usually after a month), drop the backup:

```bash
docker compose exec -e PGPASSWORD=$POSTGRES_PASSWORD -T db \
    dropdb -U odoo school_prod_old
```

## Rolling back

If the upgrade goes sideways mid-flight, you have three options:

1. **Rename trick** (fastest): `ALTER DATABASE school_prod RENAME TO school_prod_broken; ALTER DATABASE school_prod_old RENAME TO school_prod;` — restore service in 30 seconds.
2. **Restore from pg_dump** (~10–20 min for a small school): drop the broken DB, recreate, pg_restore.
3. **Switch image tag back** (if you haven't touched the DB yet): revert `docker-compose.yml` to `odoo:19.0`, `docker compose up -d`.

Always have a tested rollback path before you start the upgrade.

## Next steps

- [Backup and restore →](01-backup-and-restore.md)
- [Reference: Odoo 19 specifics →](../reference/odoo-19-specifics.md)
