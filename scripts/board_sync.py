#!/usr/bin/env python3
"""Keep the cumlg group board in sync with every workstream repo.

Adds any open issue that isn't on the board yet, sets its Project field from
the repo-name prefix, and puts new items in Backlog. Never overwrites a Status
a student has already set — this only ever fills in blanks.

Run locally with:  GH_TOKEN=<pat> python scripts/board_sync.py [--dry-run]
"""

import json
import os
import sys
import urllib.error
import urllib.request

ORG = "cumlg"
PROJECT_NUMBER = 1
API = "https://api.github.com/graphql"

# Repo-name prefix -> value of the board's "Project" single-select field.
# A repo whose prefix isn't listed here is ignored, so infra repos
# (handbook, .github, lab-toolkit, project-template) stay off the board.
PREFIX_TO_PROJECT = {"decra": "DECRA", "linkage": "Linkage", "dot": "DoT"}

NEW_ITEM_STATUS = "Backlog"

DRY_RUN = "--dry-run" in sys.argv


def gql(query, **variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "Content-Type": "application/json",
            "User-Agent": "cumlg-board-sync",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        sys.exit(f"GitHub API returned HTTP {exc.code}: {exc.read().decode()[:400]}")
    if "errors" in payload:
        sys.exit(f"GraphQL error: {json.dumps(payload['errors'])[:600]}")
    return payload["data"]


PROJECT_Q = """
query($org:String!, $num:Int!, $cursor:String) {
  organization(login:$org) {
    projectV2(number:$num) {
      id title
      fields(first:50) {
        nodes { ... on ProjectV2SingleSelectField { id name options { id name } } }
      }
      items(first:100, after:$cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          fieldValues(first:20) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue {
                name field { ... on ProjectV2FieldCommon { name } }
              }
            }
          }
          content { ... on Issue { id } ... on PullRequest { id } }
        }
      }
    }
  }
}
"""

REPOS_Q = """
query($org:String!, $cursor:String) {
  organization(login:$org) {
    repositories(first:50, after:$cursor, isArchived:false) {
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        issues(first:100, states:OPEN) { nodes { id number title } }
      }
    }
  }
}
"""

ADD_M = """
mutation($project:ID!, $content:ID!) {
  addProjectV2ItemById(input:{projectId:$project, contentId:$content}) { item { id } }
}
"""

SET_M = """
mutation($project:ID!, $item:ID!, $field:ID!, $option:String!) {
  updateProjectV2ItemFieldValue(
    input:{projectId:$project, itemId:$item, fieldId:$field,
           value:{singleSelectOptionId:$option}}
  ) { projectV2Item { id } }
}
"""


def load_project():
    """Return (project_id, fields, items) walking the item pagination."""
    project_id, fields, items, cursor = None, None, [], None
    while True:
        data = gql(PROJECT_Q, org=ORG, num=PROJECT_NUMBER, cursor=cursor)
        proj = data["organization"]["projectV2"]
        if project_id is None:
            project_id = proj["id"]
            fields = {f["name"]: f for f in proj["fields"]["nodes"] if f}
        items.extend(proj["items"]["nodes"])
        page = proj["items"]["pageInfo"]
        if not page["hasNextPage"]:
            return project_id, fields, items
        cursor = page["endCursor"]


def load_repos():
    repos, cursor = [], None
    while True:
        data = gql(REPOS_Q, org=ORG, cursor=cursor)
        block = data["organization"]["repositories"]
        repos.extend(block["nodes"])
        if not block["pageInfo"]["hasNextPage"]:
            return repos
        cursor = block["pageInfo"]["endCursor"]


def option_id(field, name):
    for opt in field["options"]:
        if opt["name"].lower() == name.lower():
            return opt["id"]
    sys.exit(f"Board field {field['name']!r} has no option named {name!r}")


def field_value(item, field_name):
    for fv in item["fieldValues"]["nodes"]:
        if fv and fv.get("field", {}).get("name") == field_name:
            return fv.get("name")
    return None


def main():
    if not os.environ.get("GH_TOKEN"):
        print("GH_TOKEN is not set - skipping board sync.")
        print("Add a BOARD_SYNC_TOKEN secret to enable it (see scripts/README.md).")
        return

    project_id, fields, items = load_project()
    status_f, project_f = fields["Status"], fields["Project"]

    # content node id -> board item, so we can tell what's already tracked
    on_board = {i["content"]["id"]: i for i in items if i.get("content")}
    print(f"Board has {len(on_board)} tracked items.")

    added = filled = 0
    for repo in load_repos():
        prefix = repo["name"].split("-")[0].lower()
        project_name = PREFIX_TO_PROJECT.get(prefix)
        if not project_name:
            continue
        proj_opt = option_id(project_f, project_name)

        for issue in repo["issues"]["nodes"]:
            existing = on_board.get(issue["id"])
            label = f"{repo['name']}#{issue['number']}"

            if existing is None:
                if DRY_RUN:
                    print(f"  would add     {label}")
                    added += 1
                    continue
                item_id = gql(ADD_M, project=project_id, content=issue["id"])[
                    "addProjectV2ItemById"
                ]["item"]["id"]
                gql(SET_M, project=project_id, item=item_id,
                    field=project_f["id"], option=proj_opt)
                gql(SET_M, project=project_id, item=item_id, field=status_f["id"],
                    option=option_id(status_f, NEW_ITEM_STATUS))
                print(f"  added         {label} -> {project_name} / {NEW_ITEM_STATUS}")
                added += 1

            elif field_value(existing, "Project") is None:
                # Already tracked but missing its Project - fill the blank,
                # and leave whatever Status the owner has chosen alone.
                if DRY_RUN:
                    print(f"  would set     {label} -> {project_name}")
                else:
                    gql(SET_M, project=project_id, item=existing["id"],
                        field=project_f["id"], option=proj_opt)
                    print(f"  set Project   {label} -> {project_name}")
                filled += 1

    verb = "would add" if DRY_RUN else "added"
    print(f"Done: {verb} {added}, filled {filled} blank Project fields.")


if __name__ == "__main__":
    main()
