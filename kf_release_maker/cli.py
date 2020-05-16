#!/usr/bin/env python

import os
import re
import shutil
import tempfile

import click
from github import Github
from github.GithubException import UnknownObjectException

from kf_release_maker import config
from kf_release_maker.release_maker import (
    MAJOR,
    MINOR,
    PATCH,
    GitHubReleaseNotes
)

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
CHANGEFILE = "CHANGELOG.md"


def new_changelog(repo, release_type, github_token, blurb_file):
    """
    Creates release notes markdown containing:
    - The next release version number
    - A changelog of Pull Requests merged into master since the last release
    - Emoji and category summaries for Pull Requests in the release

    Then merges that into the existing changelog.
    """
    # Build notes for new changes

    blurb = None
    if blurb_file:
        with open(blurb_file, "r") as bf:
            blurb = bf.read().strip()

    new_version, new_markdown = GitHubReleaseNotes().build_release_notes(
        repo=repo,
        release_type=release_type,
        gh_token=github_token,
        blurb=blurb,
    )

    print("=" * 32 + "BEGIN DELTA" + "=" * 32)
    print(new_markdown)
    print("=" * 33 + "END DELTA" + "=" * 33)

    if new_version not in new_markdown.partition("\n")[0]:
        print(
            f"New version '{new_version}' not in release title of new markdown."
        )
        return None, None, None

    # Load previous changelog file

    gh_repo = Github(github_token).get_repo(repo)
    try:
        prev_markdown = gh_repo.get_contents(CHANGEFILE).decoded_content.decode(
            "utf-8"
        )
    except UnknownObjectException:
        prev_markdown = ""

    # Remove previous title line if not specific to a particular release

    if "\n" in prev_markdown:
        prev_title, prev_markdown = prev_markdown.split("\n", 1)
        if re.search(r"[Rr]elease .*\d+\.\d+\.\d+", prev_title):
            prev_markdown = "\n".join([prev_title, prev_markdown])

    # Update changelog with new release notes

    if new_version in prev_markdown.partition("\n")[0]:
        print(f"\nNew version '{new_version}' already in {CHANGEFILE}.")
        return None, None, None
    else:
        changelog = "\n\n".join([new_markdown, prev_markdown]).rstrip()
        print()
        print("=" * 30 + "BEGIN CHANGELOG" + "=" * 30)
        print(changelog)
        print("=" * 31 + "END CHANGELOG" + "=" * 31)
        return new_version, new_markdown, changelog


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """
    Container for the cli
    """
    pass


def options(function):
    function = click.option(
        "--blurb_file",
        prompt="Markdown file containing a blurb to prepend to the notes for this release",
        default="",
        help="Markdown file containing a blurb to prepend to the notes for this release",
    )(function)
    function = click.option(
        "--release_type",
        default="minor",
        type=click.Choice([MAJOR, MINOR, PATCH]),
        prompt="What kind of release is this?",
        help="Version types follow semantic versioning",
    )(function)
    function = click.option(
        "--repo",
        prompt="The github repository (e.g. my-organization/my-project-name)",
        help="The github organization/repository to make a release for",
    )(function)
    return function


@click.command(
    name="preview", short_help="Preview the changes for a new release"
)
@options
def preview_changelog_cmd(repo, release_type, blurb_file):
    github_token = os.getenv(config.GH_TOKEN_VAR)
    new_changelog(repo, release_type, github_token, blurb_file)


@click.command(name="build", short_help="Generate a new release on GitHub")
@options
@click.option(
    "--project_title",
    prompt="The title of the project",
    default="",
    help="This will be put before the release number in the generated notes",
)
@click.option(
    "--pre_release_script",
    prompt="Shell script to run before pushing the release to GitHub",
    default="",
    help="Shell script to run before pushing the release to GitHub",
)
def make_release_cmd(
    repo, release_type, project_title, blurb_file, pre_release_script
):
    github_token = os.getenv(config.GH_TOKEN_VAR)
    new_version, new_markdown, changelog = new_changelog(
        repo, release_type, github_token, blurb_file
    )

    if changelog:
        # Attach project header
        changelog = f"# {project_title} Change History\n\n{changelog}"

        # Freshly clone repo
        tmp = os.path.join(tempfile.gettempdir(), "release_maker")
        shutil.rmtree(tmp, ignore_errors=True)
        print(f"Cloning https://github.com/{repo}.git to {tmp} ...")
        os.system(
            f"git clone --quiet --depth 1 https://{github_token}@github.com/{repo}.git {tmp}"
        )
        os.chdir(tmp)

        print("Writing updated changelog file ...")
        with open(CHANGEFILE, "w") as cl:
            cl.write(changelog)

        if pre_release_script:
            print(f"Executing pre-release script {pre_release_script} ...")
            os.chmod(pre_release_script, "u+x")
            os.system(pre_release_script)

        # Create and push new release branch
        release_branch_name = f"🔖-release-{new_version}"
        print(f"Submitting release branch {release_branch_name} ...")
        os.system(f"git checkout --quiet -b {release_branch_name}")
        os.system("git add -A")
        os.system(f"git commit --quiet -m ':bookmark: Release {new_version}\n\n{new_markdown}'")
        os.system(f"git push --quiet -f origin {release_branch_name}")

        # Create GitHub Pull Request
        print("Submitting PR for release ...")
        gh_repo = Github(github_token).get_repo(repo)
        pr_title = f"🔖 Release {new_version}"
        pr_url = None
        for p in gh_repo.get_pulls(state="open", base="master"):
            if p.title == pr_title:
                pr_url = p.html_url
                break

        if pr_url:
            print(f"Updated release PR: {pr_url}")
        else:
            pr = gh_repo.create_pull(
                title=pr_title,
                body=new_markdown,
                head=release_branch_name,
                base="master",
            )
            pr.add_to_labels("release")
            print(f"Created release PR: {pr.html_url}")
    else:
        print("Doing nothing.")


cli.add_command(preview_changelog_cmd)
cli.add_command(make_release_cmd)
