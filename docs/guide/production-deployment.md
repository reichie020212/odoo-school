# Production deployment

This guide walks through deploying the `odoo-school` suite to a production server using the committed Docker Compose stack (`docker-compose.yml` + `docker-compose.prod.yml`). The dev overlay (`docker-compose.override.yml`) is **only** for local development and must be excluded on production hosts.

## 1. Prerequisites

On the production host:

- Linux server with a recent kernel (Ubuntu 22.04+ / Debian 12 / similar).
- Docker Engine 24+ and the Compose plugin (`docker compose` v2).
- Outbound network access to pull `postgres:16-alpine` and `odoo:19.0` base images.
- A DNS name pointing at the host (e.g. `school.example.com`) if you intend to serve over HTTPS.
- Disk space for the database and Odoo filestore volumes (plan for at least 20 GB to start).

## 2. Clone the repository

```bash
sudo mkdir -p /opt && cd /opt
sudo git clone https://github.com/reichie020212/odoo-school.git
sudo chown -R "$USER":"$USER" odoo-school
cd odoo-school
git checkout main
```

## 3. Remove the dev overlay on the prod host

`docker-compose.override.yml` is auto-loaded by `docker compose` when present in the working directory. It exposes the database on port 5433 and runs Odoo with `--dev=all` — both unsafe in production. On the production host, delete or rename it:

```bash
rm docker-compose.override.yml
```

(The file remains in git for developer machines; deleting it locally on the server keeps the working tree clean without affecting other clones.)

## 4. Configure secrets and production settings

### 4a. Database password

Create a `.env` file next to the compose files (it is gitignored). Use a long, random secret:

```bash
umask 077
cat > .env <<EOF
POSTGRES_PASSWORD=$(openssl rand -base64 32)
EOF
```

### 4b. Admin master password and DB list visibility

`odoo.conf` ships without an `admin_passwd` and with `list_db = True`. Both must change before exposing Odoo to the public internet. Edit `odoo.conf` on the prod host (do not commit prod-only changes):

```ini
[options]
addons_path = /mnt/extra-addons/odoo-school
data_dir = /var/lib/odoo
db_host = db
db_port = 5432
db_user = odoo
gevent_port = 8072
list_db = False
admin_passwd = <long-random-string>
proxy_mode = True
```

Set `proxy_mode = True` if (and only if) you will front Odoo with a reverse proxy that sets `X-Forwarded-*` headers — see step 7.

## 5. Build the production image

The prod compose file builds a local image `sms-odoo:local` from `Dockerfile`, which copies `odoo.conf` into the image. After any change to `odoo.conf` you must rebuild:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml build
```

Always pass both `-f` flags explicitly so the dev override is never picked up if it is ever re-introduced.

## 6. Launch the stack

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

This starts:

- `db` — Postgres 16, data persisted in the named volume `sms_db_data`.
- `odoo` — container named `odoo-school`, listening on `8069` (HTTP) and `8072` (gevent / websocket), filestore in the named volume `sms_odoo_filestore`, running with 2 workers.

Check status and tail logs:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f odoo
```

## 7. Initialize the database

Create the production database and install the full school suite. Installing `school_homepage` pulls in every other `school_*` module transitively.

Use `docker compose run --rm`, **not** `docker compose exec`. The Odoo image's entrypoint is what translates the `HOST` / `USER` / `PASSWORD` env vars into `--db_host` / `--db_user` / `--db_password` flags; `exec` bypasses the entrypoint and the init will fail with `fe_sendauth: no password supplied`.

### Option A — clean production database (no demo data)

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm \
  odoo odoo -d school_prod -i school_homepage --stop-after-init --without-demo=all
```

### Option B — load demo data (sample students, classrooms, fees, etc.)

There is **no `--with-demo` flag** in Odoo — demo is the default. You enable demo by **omitting** `--without-demo`:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm \
  odoo odoo -d school_prod -i school_homepage --stop-after-init
```

> **Demo is a one-shot, DB-creation-time decision.** Odoo flips a `demo` flag on the database the first time it is created and uses that flag from then on. Re-running `-i school_homepage` later without `--without-demo` will **not** add demo data to an existing no-demo DB. To switch a database from no-demo to demo (or vice versa), drop and recreate it:
>
> ```bash
> docker compose -f docker-compose.yml -f docker-compose.prod.yml stop odoo
> docker compose -f docker-compose.yml -f docker-compose.prod.yml exec db dropdb -U odoo school_prod
> # then re-run Option A or Option B above
> docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d odoo
> ```
>
> The same applies to the `without_demo` key in `odoo.conf` — it is only consulted during the first `-i` run on a non-existent database. Don't put it in `odoo.conf`; control demo per-init via the CLI flag above.

### After init

Restart the Odoo container so it picks up the freshly-installed modules under workers:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart odoo
```

Sign in at `http://<host>:8069` as `admin` / `admin` and immediately rotate the admin user password.

## 8. Reverse proxy and TLS

The compose stack does **not** ship a reverse proxy. Front Odoo with nginx, Caddy, or Traefik on the same host (or a load balancer) and terminate TLS there. Minimum requirements:

- Forward `:443` → Odoo `:8069` for HTTP traffic.
- Forward websocket upgrades → Odoo `:8072` (gevent). Path: `/websocket`. (Odoo 19 dropped the `/longpolling/*` routes — everything is websockets on the gevent port now.)
- Set `X-Forwarded-Proto`, `X-Forwarded-For`, and `X-Forwarded-Host`.
- Keep `proxy_mode = True` in `odoo.conf` (see step 4b).

Bind Odoo's published ports to `127.0.0.1` if the proxy runs on the same host — edit the `ports:` mapping in a small additional override file rather than removing it from `docker-compose.yml`.

## 9. Backups

Two pieces of state must be backed up together:

1. **Database** — `sms_db_data` volume.
2. **Filestore** (attachments, report cache) — `sms_odoo_filestore` volume.

Daily logical dump:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db \
  pg_dump -U odoo -Fc school_prod > /var/backups/odoo-school/school_prod-$(date +%F).dump
```

Filestore archive:

```bash
docker run --rm -v sms_odoo_filestore:/data -v /var/backups/odoo-school:/backup \
  alpine tar czf /backup/filestore-$(date +%F).tgz -C /data .
```

Schedule both via `cron` or a systemd timer and ship the resulting files off-host.

## 10. Updates and migrations

Pulling new code from `main`:

```bash
cd /opt/odoo-school
git pull --ff-only origin main
docker compose -f docker-compose.yml -f docker-compose.prod.yml build
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

If the update touches model definitions, security rules, or views, run an Odoo upgrade pass via `run --rm` (so the entrypoint applies the DB credentials from env):

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm \
  odoo odoo -d school_prod -u school_homepage --stop-after-init
```

Use `-u <module>` to upgrade just one module. `school_homepage` cascades updates to every dependency.

## 11. Operational reference

```bash
# Shell into the Odoo container
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec odoo bash

# Postgres shell
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec db psql -U odoo school_prod

# Stop the stack (keeps volumes)
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Stop and DESTROY data — never run on a real production host
docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v
```

## Pre-launch checklist

- [ ] `docker-compose.override.yml` deleted on the prod host.
- [ ] `.env` populated with a strong `POSTGRES_PASSWORD`, file mode 600.
- [ ] `odoo.conf` has `admin_passwd` set, `list_db = False`, `proxy_mode = True`.
- [ ] Production image built (`docker compose ... build`).
- [ ] Stack up, healthcheck passing on `db`.
- [ ] Database initialized with `--without-demo=all`.
- [ ] `admin` user password rotated.
- [ ] Reverse proxy with valid TLS certificate in front of port 8069/8072.
- [ ] Backup job scheduled for both the Postgres volume and the filestore volume.
