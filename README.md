# Kids First Release Maker

Author software releases for Kids First code repositories

## Features

The release maker currently produces a release notes markdown file for the next release. It formats version numbers with semantic versioning in mind.

Release notes markdown consists of:

- The next major, minor, or patch version of the release for a repository
- A release changelog from Pull Requests merged since the last release
- Emoji and label summaries for the Pull Requests in the release


## Installation

```
$ pip install -e git+https://GitHub.com/kids-first/kf-release-maker.git#egg=kf-release-maker
```

## Creating a new release

This is an outline of how to use the release maker to generate a new release.
For complete release authoring process, see the [Developer Handbook](https://GitHub.com/kids-first/kf-developer-handbook).

1) Install the release maker as above
2) Make sure `GH_TOKEN` is in the environemnt (Get a [GitHub token](https://GitHub.com/settings/tokens))
3) Run `release notes` to generate the release notes
4) Provide the organization of the repository. Defaults to `kids-first`.
5) Provide the name of the repository for release.
6) Specify whether the release a major, minor, or patch release. Will default to a minor release otherwise.
7) Release notes will be produced on screen and saved to a file in the current directory
8) These release notes should be prepended to the repo's `CHANGELOG.md` on a new `release-x.y.z` branch
9) All other occurrences of the version number in the repo's source code should be updated
10) The changes should be committed with commit message: `:label: Release x.y.z`
11) A PR for the branch should be made in GitHub against master with the body contents of the release notes
12) All stakeholders should approve
12) The release branch is merged into the master
13) A new GitHub release should be authored using the release notes generated here and appropriate version tag
14) The release will be published into production
