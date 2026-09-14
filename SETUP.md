# Setup — from zero to a live, self-refreshing dashboard

Follow these once. After step 5 it refreshes itself on a schedule forever.

## 1. Create the repo and push these files
- On GitHub, create a **new, empty, public** repository (public = free unlimited Actions).
- Do **not** add a README/licence on creation (keeps it empty).
- Push the contents of this folder to the `main` branch. Either:
  - **GitHub Desktop / drag-and-drop:** unzip, then upload all files to the repo, or
  - **Command line:**
    ```bash
    cd usd-monitor-repo
    git init -b main
    git add .
    git commit -m "initial: dollar monitor"
    git remote add origin https://github.com/<you>/<repo>.git
    git push -u origin main
    ```

## 2. Add your FRED API key as a secret
- Get a free key: https://fredaccount.stlouisfed.org/apikeys
- Repo **Settings → Secrets and variables → Actions → New repository secret**
  - Name: `FRED_API_KEY`
  - Value: your key

## 3. Allow Actions to commit
- Repo **Settings → Actions → General → Workflow permissions**
  - Select **Read and write permissions** → **Save**

## 4. Turn on Pages (optional but recommended)
- Repo **Settings → Pages → Build and deployment → Source → GitHub Actions**
- (If you skip this, the dashboard still refreshes as a file in the repo — Pages just publishes it to a public URL.)

## 5. Run it once
- Repo **Actions** tab → **Refresh Dollar Monitor** (left sidebar) → **Run workflow** → **Run workflow**.
- It builds (~2–3 min), then commits `site/us-dollar-monitor.html`.
- **Deploy to Pages** then runs automatically and publishes to
  `https://<you>.github.io/<repo>/`.

That's it. From now on it refreshes at 06:00 UTC on weekdays, and any time you push
a change to the models. You can always trigger a manual run from the Actions tab.

---

## How the two workflows fit together (why it won't get stuck)

- **Refresh Dollar Monitor** (`refresh.yml`) — rebuilds every model from live data and
  commits the HTML. Self-contained: no Pages, no environment, 20-minute timeout, and a
  concurrency guard so a new run cancels any stuck old one. This is the part that must
  always work, and on a public repo it will.
- **Deploy to Pages** (`deploy-pages.yml`) — runs only *after* a successful refresh and
  just publishes the committed file. If Pages is ever misconfigured or GitHub Pages is
  down, **the refresh still succeeds and the repo file still updates** — deployment is
  decoupled, so it can never wedge the build.

## If a run ever sits on "Queued"
This is almost always GitHub-side, not your config:
1. Check **githubstatus.com** — if Actions isn't green, just wait and re-run.
2. Cancel the stuck run **from inside the run's own page** (not the Actions list), let it
   go fully Cancelled, then run again.
3. Push any tiny commit to `main` to force a fresh run.
The concurrency guard + timeout in `refresh.yml` mean stuck runs now clear themselves on
the next trigger, rather than blocking.

## Verify locally (optional)
```bash
pip install -r requirements.txt
export FRED_API_KEY=...
python -m build.run          # writes site/us-dollar-monitor.html
```
