# Pull Requests

## Overview

Overview of creating a properly formatted pull request for __PROJECT_NAME__

### Intended audience

Developers

### See also

- [Issues](maintainers/work-management/issues.md)

## Create a pull request

Follow the steps [here](https://help.github.com/articles/creating-a-pull-request/) to create a pull request for the correct repository.

Don't forget to verify the target branch. By default, this is the next release branch, but your issue may need to be merged into a different branch.

Follow the format below for the title and description.

## Format a pull request

### Title

Pull request titles should be succinct and state how the PR addresses the issue.

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Must start with `[WIP]` or `[REVIEW]`

`[WIP]` denotes a PR which is still being worked on and should never be merged. This is used to solicit feedback from the community.

`[REVIEW]` denotes a PR which the author believes fully addresses the issue and is ready to be reviewed and merged.

### Description

The description must start with `Closes #[issue number]`. If the PR [addresses multiple issues](https://help.github.com/articles/closing-issues-using-keywords/#closing-multiple-issues), use an unordered and repeat `Closes #[issue number]` for each issue. For example:

```
- Closes #45
- Closes #60
```

The description should also detail the implementations, challenges, and solutions so reviewers can understand the approach. Liberally reference related pull requests and/or related issues, especially if this pull request may affect them.

The description should NOT reword the issue description.

### Comments

All comments and reviews to pull requests must follow the [Code of Conduct]({CODE_OF_CONDUCT.md)

## Lifecycle

### Merging

Once the pull request is ready, update the title to start with `[REVIEW]` and set the status to `Review` in the GitHub Project.

Assuming CI is set up: All pull requests must pass continuous integration [status checks](https://help.github.com/articles/about-status-checks/). If your PR is failing CI but you believe the problem is unrelated to your code, please leave a comment in your PR to explain why.

Pull requests are reviewed by the community and once approved, the PR is merged by an approved reviewer.
