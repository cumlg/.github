# Board sync

[`board_sync.py`](board_sync.py) keeps the group board
[**Workstreams**](https://github.com/orgs/cumlg/projects/1) in step with the
workstream repos. Every 30 minutes it:

1. finds every **open** issue in repos prefixed `decra-`, `linkage-` or `dot-`;
2. adds any that aren't on the board yet, in **Backlog**;
3. sets the **Project** field (`DECRA` / `Linkage` / `DoT`) from the repo prefix.

It only ever fills in blanks — an issue already on the board keeps whatever
**Status** its owner set. Repos without one of those prefixes (`handbook`,
`.github`, `lab-toolkit`, `project-template`) are ignored, so a new workstream
repo joins the board just by being named to the convention.

## Why this exists

GitHub's built-in *Auto-add to project* workflow is capped at **one workflow
covering one repository** on the Free plan, and the Projects API has no mutation
to create or enable those workflows. A scheduled sweep is the only thing that
covers all the repos at once — and unlike the built-in, it can set the Project
field.

## Setup — the token

`GITHUB_TOKEN` can't write to organisation projects, so this needs a PAT.

1. Go to **[github.com/settings/tokens](https://github.com/settings/tokens)** →
   *Generate new token (classic)*.
2. Name it `cumlg board sync`, set an expiry you'll remember to renew.
3. Tick **`repo`**, **`read:org`** and **`project`**.
4. Generate, copy the token, then store it on this repo:

   ```bash
   gh secret set BOARD_SYNC_TOKEN -R cumlg/.github
   ```

Until that secret exists the job exits quietly rather than failing, so it won't
send failure mail while it's waiting to be set up.

> A fine-grained PAT works too and is tighter: organisation permission
> *Projects: Read and write*, plus repository permissions *Issues: Read* and
> *Metadata: Read* on all repos. It needs org approval, which is why the classic
> token is the default recommendation here.

## Running it by hand

**Actions → Board sync → Run workflow** triggers it immediately; tick
*dry run* to see what it would change first.

Locally:

```bash
GH_TOKEN=$(gh auth token) python scripts/board_sync.py --dry-run
```

## Changing it

Adding a funding stream means adding its prefix to `PREFIX_TO_PROJECT` in
`board_sync.py` **and** adding a matching option to the board's **Project**
field — the script exits with an error if the option is missing, rather than
silently mislabelling work.
