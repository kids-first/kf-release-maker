#!/usr/bin/env python

import os
import sys

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


def options(function):
    function = click.option(
        "--repo",
        prompt="The github repository (e.g. kids-first/kf-lib-data-ingest)",
        help="The github organization/repository to make a release for",
    )(function)
    function = click.option(
        "--release_type",
        default="minor",
        type=click.Choice([MAJOR, MINOR, PATCH]),
        prompt="What kind of release is this?",
        help="Version types follow semantic versioning",
    )(function)
    function = click.option(
        "--github_token", default="", help="API token for GitHub"
    )(function)
    function = click.option(
        "--blurb_file",
        prompt="Markdown file containing a blurb to prepend to the notes for this release",
        default="",
        help="Markdown file containing a blurb to prepend to the notes for this release",
    )(function)
    return function


def release_notes(repo, release_type, github_token, blurb_file):
    """
    Create a release notes markdown file containing:

    - The next release version number

    - A changelog of Pull Requests merged into master since the last release

    - Emoji and category summaries for Pull Requests in the release
    """
    blurb = None
    if blurb_file:
        with open(blurb_file, "r") as bf:
            blurb = bf.read().strip()

    r = GitHubReleaseMaker()
    new_version, markdown = r.build_release_notes(
        repo=repo,
        release_type=release_type,
        gh_token=github_token or os.getenv(config.GH_TOKEN_VAR),
        blurb=blurb,
    )

    # Write markdown file
    file_name = f'{repo.partition("/")[2]}-{new_version}.md'
    with open(file_name, "w") as f:
        f.write(markdown)

    return new_version, markdown


def update_changelog(project_title, new_version, markdown):
    changefile = "CHANGELOG.md"

    new_first_line = markdown.partition("\n")[0]
    if new_version not in new_first_line:
        print(
            f"New version '{new_version}' not in release title of new markdown. Doing nothing."
        )
        return False

    previous = ""
    if os.path.isfile(changefile):
        with open(changefile, "r") as cl:
            previous = cl.read()
            if previous:
                previous = previous.partition("\n")[2].lstrip()  # remove title

    previous_version_line = previous.partition("\n")[0]
    print("")
    if new_version not in previous_version_line:
        title = f"# {project_title} Change History"
        markdown = "\n\n".join([title, markdown, previous]).rstrip()
        with open(changefile, "w") as cl:
            cl.write(markdown)
        print(f"Updating {changefile}.")
        return True
    else:
        print(
            f"New version '{new_version}' already in {changefile}. Doing nothing."
        )
        return False


@click.command(name="notes")
@options
def release_notes_cmd(repo, release_type, github_token, blurb_file):
    return release_notes(repo, release_type, github_token, blurb_file)


@click.command(name="changelog")
@options
@click.option(
    "--project_title",
    prompt="The title of the project",
    default="",
    help="This will be put before the release number in the generated notes",
)
def update_changelog_cmd(
    repo, release_type, project_title, github_token, blurb_file
):
    new_version, markdown = release_notes(
        repo, release_type, github_token, blurb_file
    )
    return update_changelog(project_title or repo, new_version, markdown)


cli.add_command(release_notes_cmd)
cli.add_command(update_changelog_cmd)
