#!/usr/bin/env python

import os

import click

from kf_release_maker import config
from kf_release_maker.release_maker import (
    MAJOR,
    MINOR,
    PATCH,
    GitHubReleaseMaker,
)

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """
    Kids First software release authoring tool

    This method does not need to be implemented. cli is the root group that all
    subcommands will implicitly be part of.
    """
    pass


@click.command(name="notes")
@click.option(
    "--repo",
    prompt="The github repository (e.g. kids-first/kf-lib-data-ingest)",
    help="The github organization/repository to make a release for",
)
@click.option(
    "--release_type",
    default="minor",
    type=click.Choice([MAJOR, MINOR, PATCH]),
    prompt="What kind of release is this?",
    help="Version types follow semantic versioning",
)
def release_notes(repo, release_type):
    """
    Create a release notes markdown file containing:

    - The next release version number

    - A changelog of Pull Requests merged into master since the last release

    - Emoji and category summaries for Pull Requests in the release
    """

    r = GitHubReleaseMaker()
    new_version, markdown = r.build_release_notes(
        repo=repo,
        release_type=release_type,
        gh_token=os.getenv(config.GH_TOKEN_VAR),
    )

    # Write markdown file
    file_name = f'{repo.partition("/")[2]}-{new_version}.md'
    with open(file_name, "w") as f:
        f.write(markdown)

    print(f"Saved release notes to {file_name}")


cli.add_command(release_notes)
