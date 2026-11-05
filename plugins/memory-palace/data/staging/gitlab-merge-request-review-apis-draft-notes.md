---
title: 'GitLab merge request review APIs: draft notes, publish, approve'
source:
  type: web_fetch
  identifier: https://docs.gitlab.com/api/draft_notes/
author: claude
date_captured: '2026-10-30'
palace: Engineering Practice
district: Review platforms
maturity: probation
tags:
- gitlab
- code-review
- api
- pr-review
---

# GitLab merge request review APIs: draft notes, publish, approve

## Marginal Value Summary

- **Integration Decision**: standalone
- **Confidence**: 90%
- **Novelty Tags**: gitlab, code-review, api, pr-review

## Intake Content

# GitLab merge request review APIs: draft notes, publish, approve

Sources: docs.gitlab.com/api/draft_notes/ and
docs.gitlab.com/api/merge_request_approvals/, captured 2026-10-30. Neither
page states the GitLab version that added these endpoints.

## Draft notes

`POST /projects/:id/merge_requests/:merge_request_iid/draft_notes`

`position` (optional; omitted creates a regular discussion note), with
`position[base_sha]`, `position[head_sha]`, `position[start_sha]`
(required when `position` is set), `position[new_path]` and
`position[old_path]` (required for `text`), `position[position_type]`
(`text`, `image` or `file`), `position[new_line]`, `position[old_line]`,
`position[line_range]`. The three SHAs come from
`GET .../merge_requests/:iid/versions`.

## Publish

`POST /projects/:id/merge_requests/:merge_request_iid/draft_notes/bulk_publish`

- `note`: a summary note added with the review.
- `internal`: make the summary internal.
- `reviewer_state`: `requested_changes` or `reviewed`. "Does not record a
  formal approval."

Bulk publish sends every draft the user holds on the MR, not only those
created in the current run.

## Approve

`POST /projects/:id/merge_requests/:merge_request_iid/approve` and
`.../unapprove`. The approvals page documents no request-changes
endpoint.

Relevance here: `plugins/sanctum/scripts/post_formal_review.py` uses
exactly these calls for its GitLab path, and refuses to publish when the
user already has drafts on the MR.
