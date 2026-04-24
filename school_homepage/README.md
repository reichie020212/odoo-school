# School Homepage

**Odoo 19 Community module — website-based landing page at `/` for the School Management System.**

Depends on `website` plus all `school_*` modules — installs as the final piece of the suite.

## What it does

- Registers an HTTP controller that serves `GET /` (public, website-aware) and renders a QWeb template named `school_homepage.homepage`.
- The template calls `website.layout`, so the Odoo Website app can wrap it with the standard header/footer/menu.
- Content: school identity (company name + logo), a hero with portal and staff login CTAs, a quick-stats section (counts from `res.partner`/`hr.employee`/`school.classroom`/`school.course`/`school.library.book`), a three-column feature grid, and a footer.

## Editing the homepage

Because the view is rendered via `website.layout`, administrators can:

1. Log in to the backend as a user with Website access.
2. Navigate to `/` on the public site.
3. Click **Edit** and use the Website builder to tweak copy, swap the hero image, or add snippets.

Edits are persisted on the view record — they don't need a code deploy.

## Tests

```bash
odoo-bin -d school_dev -i school_homepage --test-enable --test-tags=/school_homepage --stop-after-init
```

4 HttpCase tests verify that `/` returns HTTP 200, includes the company name, exposes portal (`/my`) and backend (`/web`) links, and renders all five stat labels.

## Dependencies

- `website`
- `school_base`, `school_academics`, `school_exams`, `school_fees`, `school_library`, `school_canteen`, `school_shop`, `school_transport`, `school_portal`, `school_comms`

Installing `school_homepage` pulls in the full School Management System — it's the "everything's wired up" module.
