# Issues

## Overview

Overview of the best practices for creating and updating issues for __PROJECT_NAME__.

### Intended audience

Community | Developers

### See also
- [Contributing Code]({CONTRIBUTING.md})
- [Pull Requests]({maintainers/work-management/prs.md})

## Create an issue

> **Warning**
> 
> Before creating an issue, please search existing open & closed issues and pull requests to see if your issue has already been addressed.

Follow the steps [here](https://help.github.com/articles/creating-an-issue/) to start the process of creating an issue.

Issues in __PROJECT_NAME__ projects fall into 3 primary types. When creating the issue, select the best fit from these options:

| Issue type | Title Prefix | Description |
|:-----------|:-------------|:------------|
| Bug | `[BUG]` | Report a problem with the code |
| Documentation | `[DOC]` | Report a problem or suggestion related to documentation
| Feature | `[FEA]` | Suggest an new idea or enhancement |

There may also be:
| Issue type | Title Prefix | Description |
|:-----------|:-------------|:------------|
| Question | `[QST]` | Ask a general question - GitHub Discussions may be used instead of this issue type |
| Epic | `[EPIC]` | Large-reaching issues that contain [tasklists](https://docs.github.com/en/issues/tracking-your-work-with-issues/about-tasklists) of component issues


If you have an issue which truly is not one of the above, you can select `Open a regular issue`. During triage, the team may ask the filer to resubmit the issue as a template if found to be incorrecly un-templated.

Consider adding https://github.com/jarmak-nv/rapids-repo-template/labels/good%20first%20issue or https://github.com/jarmak-nv/rapids-repo-template/labels/help%20wanted labels to the issue if applicable.

## Format

### Title

Use the appropriate type prefix outlined above. This should be automatically populated when creating the issue.

The title should be succinct description of problem, feature, or question. If code related, try to include the class or function name in the title.

### Description

When using one of the issue types, the description will be populated with a template which will guide how to describe the issue.

In general, you want to fully describe the issue so that someone can fully understand and reproduce the issue. If during triage the team has any questions, they will comment on the issue for clarification.


#### Task list

If your issue is large-reaching, consider creating an epic, or defining tasks using tasklists.

As a developer works on an issue, perhaps after creating a `[WIP]` pull request, they should update the task list and mark tasks completed.

#### Blockers

If an issue is blocked due to another issue or pull request do the following:
- Set the status in the GitHub Project to `Blocked`
- Add a tasklist with an entry for each blocking issue to the top of the issue, titled `Blocked By`

## Lifecycle

Issues are either assigned by team leads or picked in priority order. When you begin work on an issue, set the status in the GitHub Project to `In Progress` and link the PR once it's up.

When the associated pull request is merged, the issue will automatically close.
