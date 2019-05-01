#!/usr/bin/env python

import os
import click

from kf_release_maker import config
from kf_release_maker.release_maker import GitHubReleaseMaker

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """
    Kids First software release authoring tool

    This method does not need to be implemented. cli is the root group that all
    subcommands will implicitly be part of.
    """
    pass


@click.command(name='notes')
@click.option('--org', default=config.DEFAULT_GH_ORG,
              prompt='Name of the github organization',
              help='Nome of the github organization containing the repository')
@click.option('--repo', default=os.getcwd().split('/')[-1],
              prompt='Name of the github repository',
              help='Nome of the github repository to make a release for')
@click.option(
    '--version_type', default='minor',
    type=click.Choice(list(config.VALID_VERSION_TYPES)),
    prompt='What kind of release is this?',
    help='Version types follow semantic versioning')
def release_notes(org, repo, version_type):
    """
    Create a release notes markdown file containing:

    - The next release version number

    - A changelog of Pull Requests merged into master since the last release

    - Emoji and category summaries for Pull Requests in the release
    """

    r = GitHubReleaseMaker()
    r.release_notes(org=org, repo=repo, version_type=version_type)


cli.add_command(release_notes)
