# GitHub PAT Setup for Cross-Repo Sync

This guide explains how to create a Personal Access Token (PAT) and wire it up
so the library repository can trigger workflows in the demo repository.

---

## What is a PAT and why do we need one?

GitHub Actions workflows can only trigger other workflows in the **same**
repository by default. To trigger a workflow in a **different** repository
(e.g. from `pydantic-schemaforms` → `pydantic-schemaforms-demo`), GitHub
requires a token that proves you own both repos. A PAT is that token.

The token is stored as a secret in the library repo and is never exposed in
logs or code.

---

## Step 1 — Create the PAT

1. Go to [github.com](https://github.com) and sign in.
2. Click your **profile picture** in the top-right corner → **Settings**.
3. Scroll to the bottom of the left sidebar and click **Developer settings**.
4. Click **Personal access tokens** → **Fine-grained tokens**.
   *(Fine-grained tokens are more secure than classic tokens — use these.)*
5. Click **Generate new token**.
6. Fill in the form:

   | Field | Value |
   |---|---|
   | **Token name** | `pydantic-schemaforms-demo-sync` |
   | **Expiration** | 90 days *(or your preferred rotation window)* |
   | **Resource owner** | `devsetgo` |
   | **Repository access** | Select **Only select repositories** → choose `devsetgo/pydantic-schemaforms-demo` |

7. Under **Permissions**, expand **Repository permissions** and set:

   | Permission | Access |
   |---|---|
   | **Contents** | Read and write |
   | **Pull requests** | Read and write |
   | **Workflows** | Read and write |

   Leave everything else at **No access**.

8. Click **Generate token** at the bottom of the page.
9. **Copy the token immediately** — GitHub only shows it once. It looks like:
   `github_pat_11ABCDEF...`

   > Store it somewhere safe (a password manager) before closing the page.

---

## Step 2 — Add the PAT as a secret in the library repo

1. Go to `https://github.com/devsetgo/pydantic-schemaforms`.
2. Click **Settings** (top tab row, not your profile settings).
3. In the left sidebar, click **Secrets and variables** → **Actions**.
4. Click **New repository secret**.
5. Fill in:

   | Field | Value |
   |---|---|
   | **Name** | `DEMO_REPO_TOKEN` |
   | **Secret** | Paste the token you copied in Step 1 |

6. Click **Add secret**.

You should now see `DEMO_REPO_TOKEN` listed under repository secrets.

---

## Step 3 — Verify the token has the right access

1. Go to `https://github.com/devsetgo/pydantic-schemaforms-demo`.
2. Click **Settings** → **Actions** → **General**.
3. Under **Workflow permissions**, confirm **Read and write permissions** is
   selected (or at minimum that pull requests can be created by Actions).

   If it is set to read-only, change it to **Read and write permissions** and
   save.

---

## Step 4 — Token rotation (important)

Fine-grained PATs expire. When the token expires the sync workflow will fail
with a 401 error. To avoid surprises:

- Set a calendar reminder **one week before** the expiration date you chose.
- When it is time, repeat Step 1 to generate a new token, then update the
  secret in Step 2 (edit the existing `DEMO_REPO_TOKEN` secret with the new
  value).
- You do **not** need to change any workflow files — they reference the secret
  by name.

---

## What happens next

Once the PAT is in place, the sync workflow in `pydantic-schemaforms` will:

1. Detect changes to `examples/shared_models.py` or `examples/templates/`
   on every push to `main`.
2. Send a `repository_dispatch` event to `pydantic-schemaforms-demo` using
   `DEMO_REPO_TOKEN`.
3. The demo repo's receiving workflow copies the updated files and opens a
   pull request for review — nothing is force-pushed.

Once the PAT is in place, complete setup with these two steps:

### Step 5 — Add the receiver workflow to the demo repo

In `pydantic-schemaforms-demo`, create the file
`.github/workflows/sync-from-library.yml` and commit it to `main`.

The workflow should trigger on `repository_dispatch` with event type
`library-sync`, check out the library at the dispatched SHA, copy the
relevant files, and open a pull request using `peter-evans/create-pull-request`
(a public action — no extra setup required).

### Step 6 — Test the end-to-end flow

Make a trivial change to `examples/shared_models.py` in this repo (e.g. fix
a comment), commit, and push to `main`. Within a minute you should see:

- A **Actions** run of `sync-to-demo.yml` in this repo — it dispatches the
  event.
- A **Actions** run of `sync-from-library.yml` in the demo repo — it opens
  a PR.

If the dispatch step fails with a 401 error, the PAT either expired or lacks
the **Workflows** permission — regenerate it following Step 1.
