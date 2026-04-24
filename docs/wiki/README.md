# Wiki.js knowledge base

This folder is a **Wiki.js-ready** tree of guides, how-tos, and reference material for the School Management System. Every page has Wiki.js-compatible YAML frontmatter (`title`, `description`, `published`, `date`, `tags`, `editor`) so you can import it directly.

## Layout

```
docs/wiki/
├── README.md                (this file — not a content page)
├── home.md                  (wiki landing page — tags "overview, index, home")
├── _assets/                 (screenshots referenced by every guide)
│   ├── 01-login.png
│   ├── 02-homepage.png
│   ├── ...
│   └── 18-portal-dashboard.png
├── getting-started/
│   ├── home.md
│   ├── 01-overview.md
│   ├── 02-installation.md
│   └── 03-first-login.md
├── admin-guides/
│   ├── home.md
│   ├── 01-adding-a-student.md
│   ├── 02-classrooms-and-cohorts.md
│   ├── 03-academics-and-courses.md
│   ├── 04-exams-and-grades.md
│   ├── 05-fees-and-invoices.md
│   ├── 06-library.md
│   ├── 07-canteen.md
│   ├── 08-communications.md
│   └── 09-portal-access.md
├── portal-guides/
│   ├── home.md
│   └── 01-student-and-guardian-dashboard.md
├── reference/
│   ├── home.md
│   ├── architecture.md
│   ├── permissions.md
│   └── odoo-19-specifics.md
└── operations/
    ├── home.md
    ├── 01-backup-and-restore.md
    └── 02-upgrading.md
```

## Importing into Wiki.js

### Option 1 — Git storage (recommended)

Wiki.js supports a Git storage module that pulls Markdown files out of a repo and serves them as pages. Point it at this repo:

1. Wiki.js → **Administration → Storage → Git**.
2. Enable the module.
3. Set **Repository URL** to your fork of this repo.
4. Set **Base Directory** to `docs/wiki`.
5. Trigger a sync. Wiki.js walks the tree and creates one page per Markdown file. `home.md` inside each folder becomes the folder index (served at `/getting-started`, `/admin-guides`, etc.).

Assets in `_assets/` are served by Wiki.js as attached images; the relative `![alt](../_assets/foo.png)` links in each page resolve correctly.

### Option 2 — Upload via the "Import from Disk" module

1. Install the Wiki.js **Disk** storage module.
2. Copy `docs/wiki/` onto the Wiki.js server as its root content directory.
3. Trigger a full scan.

### Option 3 — Copy/paste per page

For quick evaluation, open each `.md` in this repo, copy the body (without frontmatter if you already set the page meta in the Wiki.js editor), and paste into a new Wiki.js page. Tedious but works.

## Page-to-URL mapping

Wiki.js by default maps `folder/file.md` to the URL `/folder/file`. Our `home.md` files become the folder index:

| File | Resulting Wiki.js URL |
|---|---|
| `home.md` | `/home` (or `/` if set as site home) |
| `getting-started/home.md` | `/getting-started` |
| `getting-started/01-overview.md` | `/getting-started/01-overview` |
| `admin-guides/01-adding-a-student.md` | `/admin-guides/01-adding-a-student` |
| `_assets/02-homepage.png` | `/_assets/02-homepage.png` (served as asset) |

The intra-wiki links in every page use **relative paths** (`../_assets/...`, `./02-installation.md`), which Wiki.js resolves correctly regardless of where in your site the wiki is mounted.

## Keeping it up to date

When the School Management System changes:

- **New feature / workflow** → add a new page under `admin-guides/` or update an existing one.
- **UI screenshot out of date** → retake it with Playwright from a fresh install with demo data (see `docs/plan/` for the capture sequence used initially).
- **Odoo major upgrade** → the [Odoo 19 specifics](reference/odoo-19-specifics.md) page needs wholesale review.

After edits, commit as normal. If you're on the Git storage module, Wiki.js picks up changes on its sync interval (configurable, default 5 min).

## Screenshots

The 18 screenshots under `_assets/` were captured against a fresh `school_dev` database with demo data enabled, using Playwright via the MCP server. They show the system exactly as a new install presents it. Keep filenames in numeric prefix order so the file browser sorts them in the same order they appear in the guides.

## Contributing

PRs adding new how-tos or correcting existing ones are welcome. House style:

- Each page begins with Wiki.js frontmatter.
- Use sentence case for headings.
- Reference other pages via relative paths so links survive folder moves.
- Put screenshots in `_assets/` with a two-digit numeric prefix.
- Keep pages focused — one workflow per page. Link between them rather than cramming everything into one giant doc.
