# __PLC_OSS__ Standard Repo Template

This is repo is the standard NVIDIA OSS repo with the following items to make all NVIDIA repos use a consistent base:

- GitHub File Templates
  - Issue templates
  - PR template
- GitHub Repo Templates
  - Issue/PR labels
  - Project tracking and release board templates
- Files
  - Root
    - `CITATION.md` with RAPIDS info pre-filled
    - `CHANGELOG.md` skeleton
    - `CODE_OF_CONDUCT.md` file with our standard code of conduct
    - `CONTRIBUTING.md` skeleton
    - `LICENSE` file with Apache 2.0 License
      - Use the [Confluence page](https://confluence.nvidia.com/pages/viewpage.action?pageId=788418816) for other licenses 
    - `print_env.sh` for debugging support
    - `README.md` skeleton
    - `SECURITY.md` file with our standard security instructions
    - `CLA.md` file (delete if not using MIT or BSD licenses)
  - Root/.github
    - /ISSUE_TEMPLATE
      - Templates for each issue type (`Bug`, `Doc`, `Feature`, `Question`)
      - `config.yml`
    - /workflow-templates
      - `add_issue_to_project.yml`
      - `add_issue_to_project_raw.yml`
      - `CODEOWNERS`
      - `PULL_REQUEST_TEMPLATE.md`
  - Root/maintainers
    - See the readme in this folder for specifics


## Usage for new NVIDIA OSS repos

1. Clone this repo
1. Find/replace all in the clone of `___PROJECT___` and `__PROJECT_NAME__` and replace with the name of the new library
1. Inspect all files to make sure all replacements work and update text as needed
1. Customize issue/PR templates to fit the repo
    - There are two issue template formats provided, simple `.md` templates and more interactive `.yml` form templates
    - Delete the overlapping templates you are not using (ie if you decide to use the `.yml`s delete the `.md` templates
    - In `config.yml` determine if you will allow issues to be created outside of the templates
    - In `config.yml` determine if you will use question issue types, or use GitHub discussions 
1. Update `CHANGELOG.md` with next release version
1. Add developer documentation to the end of the `CONTRIBUTING.md` that is project specific and useful for developers contributing to the project
    - The goal here is to keep the `README.md` light, so the development/debugging information should go in `CONTRIBUTING.md`
1. Complete `README.md` with project description, quick start, install, and contribution information
1. Copy the [template project](https://github.com/orgs/rapidsai/projects/80/views/1) into your org and name as appropriate
    - Follow the instructions in the project's [readme](https://github.com/orgs/rapidsai/projects/80/views/1?pane=info) to add your issues
    - Update your project's readme as fits best for your team
    - Use the URL of the newly created project in the `.github/workflow-templates/add_to_project.yml` GHA automations
. Check `LICENSE` file is correct (update year) 
. Change git origin to point to new repo and push
. Remove the line break below and everything above it

## Usage for existing NVIDIA OSS repos

1. Follow the steps 1-8 above, but add the files to your existing repo and merge

<!-- REMOVE THE LINE BELOW AND EVERYTHING ABOVE -->
-----------------------------------------
# [Project Title]

# Overview
Provide an overview of the project.
What the project does?
Why the project is useful?

# Get Started
Describe the get-started or installation guidelines or provide a link to the installation instruction

# Contribution Guidelines
Provide the link to the CONTRIBUTING file(s).

# Community
Provide the channel for community communications.

# References
Provide a list of related references

# License
This project is licensed under the [NAME HERE] License - see the LICENSE.md file for details

