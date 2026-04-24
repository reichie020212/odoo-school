---
title: Backup and restore
description: Dump and restore the school_* databases safely
published: true
date: 2026-04-25
tags: operations, backup, postgres
editor: markdown
---

# Backup and restore

Odoo's database manager at `/web/database/manager` ships a "Backup" button that produces a `.zip` with the DB dump plus the filestore. For day-to-day backups, that's what you want. For scripted / automated backups, use `pg_dump` directly.

## Daily backup via the web UI

1. Visit `http://<host>/web/database/manager`.
2. Find the DB row. Click **Backup**.
3. Enter the Odoo master password (defined by `admin_passwd` in `odoo.conf`, or `admin` by default in dev).
4. Format: **zip (includes filestore)** — recommended for restoring anywhere. `pg_dump custom` is smaller but Postgres-version-coupled.
5. Download.

Restore is the parallel **Restore Database** button in the same view.

## Scripted backup via `pg_dump`

Run this on your host (or a cron job on the same machine as the DB container):

```bash
set -euo pipefail
DB=school_prod
DATE=$(date +%Y-%m-%d-%H%M%S)
OUT=/var/backups/odoo-school/${DB}-${DATE}

mkdir -p "$OUT"

# 1. Dump the SQL
docker compose exec -e PGPASSWORD=$POSTGRES_PASSWORD -T db \
    pg_dump -U odoo -d "$DB" -Fc -f "/tmp/${DB}.dump"
docker compose cp "$(docker compose ps -q db)":/tmp/${DB}.dump "$OUT/${DB}.dump"

# 2. Grab the filestore (attachments, QWeb-rendered PDFs, etc.)
docker compose exec -T odoo tar -C /var/lib/odoo -czf /tmp/filestore.tar.gz filestore/$DB
docker compose cp "$(docker compose ps -q odoo)":/tmp/filestore.tar.gz "$OUT/filestore.tar.gz"

# 3. Prune backups older than 30 days
find /var/backups/odoo-school -type d -mtime +30 -exec rm -rf {} +
```

Store both files. Without the filestore, report-card PDFs and attachments on records won't survive the restore (the DB references filestore files by hash).

## Restoring from a `pg_dump`

```bash
DB_NEW=school_restored
docker compose exec -e PGPASSWORD=$POSTGRES_PASSWORD -T db \
    createdb -U odoo "$DB_NEW"

docker compose cp "$OUT/${DB}.dump" "$(docker compose ps -q db)":/tmp/${DB}.dump
docker compose exec -e PGPASSWORD=$POSTGRES_PASSWORD -T db \
    pg_restore -U odoo -d "$DB_NEW" /tmp/${DB}.dump

# Restore filestore
docker compose cp "$OUT/filestore.tar.gz" "$(docker compose ps -q odoo)":/tmp/filestore.tar.gz
docker compose exec -T odoo sh -c "cd /var/lib/odoo && tar -xzf /tmp/filestore.tar.gz"

# If the DB name changed, rename the filestore folder inside the container
docker compose exec -T odoo mv /var/lib/odoo/filestore/school_prod /var/lib/odoo/filestore/${DB_NEW}
```

Restart Odoo after a restore to clear the registry cache:

```bash
docker compose restart odoo
```

## What a backup includes

- Every `school.*` record (students, grades, fees, loans, etc.).
- `res.partner`, `hr.employee` with the school-extended fields.
- `account.move` (invoices generated from fee enrollments).
- `calendar.event` (sessions).
- `ir.config_parameter` (including the admission-number sequence state and library fine rates).
- `ir.sequence.date_range` rows — so your admission numbers don't reset on restore.
- Mail templates, automation rules, chatter messages, scheduled emails.

## What a backup does NOT include

- `.env` and `docker-compose*.yml` — keep these in your dotfiles / infrastructure repo.
- The addons code itself — that's in git.
- The Docker images — pullable from Docker Hub.

**A full recovery** therefore needs: (a) the backup, (b) the git repo at the commit you were on, and (c) your `.env` / compose config. Keep all three in safe places.

## Testing a backup

Periodically restore a backup to a throwaway DB:

```bash
docker compose run --rm --no-deps odoo odoo \
    -d school_restore_test --stop-after-init
```

Then poke around at `http://localhost:8069/?db=school_restore_test` to verify the data is intact — run a few reports, check a report card PDF, inspect a recent invoice.

## Off-site backups

Use `rsync` / `rclone` / `restic` to ship the `/var/backups/odoo-school/` directory to S3, Backblaze B2, or another server. The dumps are compressible; `-Fc` already uses pg_dump's custom format which is smaller than plain SQL.

## Next steps

- [Upgrading Odoo between versions →](02-upgrading.md)
- [Monitoring and logs →](03-monitoring.md) (TODO)
