# Issues

## Overview
__PROJECT_NAME__ Makes heavy use of the new and significantly enhanced [GitHub Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects). 

Their documentation is very good, and for a less opinionated overview we recommend exploring the docs (linked above).

### Intended audience

Project Leads | Community | Developers

### See also
- [Issues](maintainers/work-management/issues.md)
- [Pull Requests]({maintainers/work-management/prs.md)
- [Triage](maintainers/work-management/issue_triage.md)

## Accessing the project

The project can be accessed in multiple ways by clicking on the `Projects` tab within the repo and then selecting the project. It is also linked in the [readme](README.md)

## Project Setup
To Projects, we add the following custom fields:
- Release - single selection dropdown with the following fields
  - ‘Product Backlog’
  - ‘Prioritized for Future Release’ [Optional]
  - ‘XX.YY’ (Version Number)
  - As time goes on, this dropdown expands and contains all releases since the project was created
- In the Status field add ‘Review’ as a status
- (Optional) Issue Type - single selection dropdown with the following fields presented for reference, use whatever your team uses
  - ‘Bug’
  - ‘Documentation’
  - ‘Question’
  - ‘Feature Request’
- (Optional) Points - single selection dropdown with the following fields
  - 1, 2, 3, 5, 8, 13, 21
  - These are story points, they are a unitless effort estimation for issues - Fibonacci sequencing is common to decrease granularity
  - [More background on story points](https://www.scrum.org/resources/blog/practical-fibonacci-beginners-guide-relative-sizing)
- (Optional) Custom fields relevant to your project
  - Ex: Epic, Category, Dates

> **Note**
> 
> Projects can have any number of custom fields, however it is recommended to limit to as few as necessary.
> This is because custom fields from one Project do not persist to another Project, so that information can only be accessed in a limited way. 

## Project Views
By default we recommend 5 base views in the Project
- Triage - this view filters to only show open issues that have the ‘? - Needs Triage’ label
- Release board - this is a traditional Kanban board showing progress for the current release (filter by Roadmap to the current release)
- Open Issues - this view shows all open issues and groups them by the Issue Type
- Roadmap - this view shows issues grouped by release/backlog queue
- Epics - this view groups by `Tracks-By`, a feature of task-lists, giving a higher level view to the work being done
- Projects can have up to 42 views, and they are URL-linkable so links to specific views can easily be created

