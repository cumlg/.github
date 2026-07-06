# Curtin ML Group — Handbook

The one-stop reference for how we work. Edit via pull request.

## Where things go (tool routing)
| Thing | Home |
|---|---|
| Code, tasks, experiments, technical decisions, Q&A | **GitHub** (issues, PRs, this org) |
| Progress tracking | **Project board**: "Workstreams — Qilin Li" |
| Image datasets + labelling | **Roboflow** |
| Experiment runs & metrics | **Weights & Biases** |
| Large data / 3D / checkpoints | **DVC** → institutional storage |
| Drafts | **Overleaf** |
| References | Shared **Zotero** |
| Official / external / long | **Email** |

## Repositories
- One repo per **workstream**, named `<grant>-<workstream>` (e.g. `linkage-crack-detection`).
- `project-template` — start new repos from this ("Use this template").
- `lab-toolkit` — shared code; import from here instead of copying.

## Weekly rhythm
- **Monday:** move your issues into "This week" and post a 3-line update (did / doing / blocked) on your weekly-log issue.
- **During the week:** discuss in issue comments (not email); open a PR when ready.
- Meetings run off the board.

## Issues & PRs
- One issue per task/experiment. Use the **Experiment** form for runs (records hypothesis, dataset version, W&B link, result).
- Branch per issue → PR → review → merge. Link with `Closes #`.

## Using AI (Claude Code, Copilot, etc.)
- Allowed for code, drafting, and debugging. **You must understand and be able to defend every line.**
- Flag AI-generated results as such; the supervisor is the final arbiter of what ships.
- Never paste unpublished partner/DoT data into external tools without checking the data agreement.

## Onboarding a new member
1. Accept the org + team invite; enable 2FA.
2. Create your repo from `project-template`.
3. Read this handbook and your repo's `CLAUDE.md`.
4. Your first issue is an "Onboarding checklist".
