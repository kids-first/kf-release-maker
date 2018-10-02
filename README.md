# Kids First Release Maker

Author software releases for Kids First code repositories

## Features

The relase maker will:

- Mint the next major or minor version release for a repository
- Generate a changelog from PRs merged since the last release
- Generate emoji and label summaries


## Installation

```
git clone git@github.com:kids-first/kf-release-maker.git
cd kf-release-maker
pip install .
```

## Creating a new release

This is an outline of how to use the release maker to generate a new release.
For complete release authoring process, see the [Developer Handbook](https://github.com/kids-first/kf-developer-handbook).

1) Install the release maker as above
2) Make sure `GH_TOKEN` is in the environemnt (Get a [github token](https://github.com/settings/tokens))
3) Run `release`
4) Provide the organization of the repository. Defaults to `kids-first`.
5) Provide the name of the repository for release.
6) Tell whether the release as a major release. Will default to a minor release otherwise.
7) Release notes will be produced on screen and saved to a file in the current directory
8) These release notes shoud be prepended to the repo's `CHANGELOG.md` on a new `release-x.y.z` branch
9) All other occurences of the version number in the repo's source code should be updated
10) The changes should be commited with commit message: `:label: Release x.y.z`
11) A PR for the branch should be made in github against master with the body contents of the release notes
12) All stakeholders should approve
12) The release branch is merged into the master
13) A new github release should be authored with using the release notes generated here and appropriate version tag
14) The release will be published into production
