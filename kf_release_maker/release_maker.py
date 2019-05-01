import os
from urllib.parse import urlencode
from pprint import pformat

import pandas
import requests

from kf_release_maker import config


def get_gh_token(token_env_var=config.GH_TOKEN_VAR):
    """
    Get GH token from environment
    """
    token = os.environ.get(token_env_var, None)
    if token is None:
        raise Exception(
            'Please provide a github token in the GH_TOKEN env var')

    return token


def get(session, url, exit_on_fail=True, **request_kwargs):
    """
    If response.status_code is not 200 and exit_on_fail=True then exit program
    Otherwise return original response
    """
    response = session.get(url, **request_kwargs)

    if response.status_code != 200:
        print(f'Could not fetch {url}! Caused by: {response.text}')
        if exit_on_fail:
            exit(1)

    return response


def paginate(session, endpoint, query_params):
    """
    Paginate endpoint, return all results
    """
    query_params.update({'page': 1, 'per_page': 100})
    url = f'{endpoint}?{urlencode(query_params)}'
    items = True
    results = []
    while items:
        print(f'Fetching page {query_params["page"]} ...')
        url = f'{endpoint}?{urlencode(query_params)}'
        items = get(session, url).json()
        results.extend(items)
        query_params['page'] += 1

    return results


class GitHubReleaseMaker(object):

    def __init__(self, gh_api=config.DEFAULT_GH_API):
        self.api = gh_api
        self.base_url = None
        self.org = None
        self.repo = None

    def get_prs(self):
        """
        Get all closed PRs with base branch = master
        """
        print(f'Fetching PRs for {self.repo} ...')

        endpoint = f'{self.base_url}/pulls'
        query_params = {'base': 'master', 'state': 'closed'}
        prs = paginate(self.session, endpoint, query_params)

        print(f'Found {len(prs)} PRs')

        return prs

    def get_tags(self):
        """
        Get all tags
        """
        tags_url = f'{self.base_url}/tags'

        print(f'Fetching tags for {tags_url} ...')
        tags = get(self.session, tags_url).json()
        print(f'Found {len(tags)} tags')

        return tags

    def get_commit_date(self, commit_url):
        """
        Get date of commit at commit_url
        """
        latest_commit_date = ''
        latest_commit = get(self.session, commit_url).json()
        latest_commit_date = latest_commit['commit']['committer']['date']

        return latest_commit_date

    def get_last_tag(self):
        """
        Get latest tag, latest commit of the tag, and the version number
        """
        # Get all tags
        tags = self.get_tags()

        # Get latest commit of last tagged release
        if len(tags) > 0:
            latest_tag = {'version_number': tags[0]['name']}
            latest_tag['commit_date'] = self.get_commit_date(
                tags[0]['commit']['url'])
            print(f'Last tag was: {latest_tag["version_number"]}, '
                  f'last commit was: {tags[0]["commit"]["sha"]}, '
                  f'committed on : {latest_tag["commit_date"]}')
        else:
            print('No tags exist yet')
            latest_tag = {'version_number': '0.0.0',
                          'commit_date': ''}

        return latest_tag

    def make_pr_df(self, prs, latest_tag):
        """
        Make Pull Requests DataFrame with content needed to make
        release notes markdown
        """
        pr_df = pandas.DataFrame([
            {
                'title': pr['title'],
                'merged_at': pr['merged_at'],
                'user': pr['user'].get('login'),
                'number': pr['number'],
                'label_link': pr['labels'][0]['url'] if pr['labels'] else None
            }
            for pr in prs
        ])
        print('Filtering out PRs that closed but did not merge into master')
        pr_df = pr_df[pr_df['merged_at'].notnull()]

        print('Filtering out release PRs')
        pr_df = pr_df[(~pr_df['title'].str.startswith(config.RELEASE_EMOJI) &
                       ~pr_df['title'].str.contains('Release'))]

        # Only include PRs after latest commit of last tagged release
        if latest_tag['commit_date']:
            print('Filtering out PRs before last release on '
                  f'{latest_tag["commit_date"]}')
            pr_df = pr_df[pr_df['merged_at'] > latest_tag['commit_date']]

        print(f'Remaining PRs: {pr_df.shape[0]}')

        # Extract PR emojis, add them into own column
        def get_emoji(title):
            parts = title.split(' ', 2)
            if len(parts) < 2:
                return config.EMOJI_NOT_FOUND
            else:
                return parts[0]
        pr_df['emoji'] = pr_df['title'].apply(
            lambda title: get_emoji(title))

        # Categorize PR emojis, add categories into own column
        pr_df['category'] = pr_df['emoji'].apply(
            lambda emoji: config.EMOJI_CATEGORIES.get(
                emoji,
                config.EMOJI_CATEGORIES['default'])
        )

        return pr_df

    def next_release_version(self, prev_version, version_type):
        """
        Get next release version based on prev version. Version # uses
        semantic versioning

        version_type must be one of {'major', 'minor', 'patch'}
        """
        if version_type not in config.VALID_VERSION_TYPES:
            raise ValueError(
                f'Invalid version type: {version_type}! Version type '
                f'must be one of {pformat(config.VALID_VERSION_TYPES)}!'
            )

        parts = [int(p) for p in prev_version.split('.')]
        if version_type == 'major':
            new_version = f'{parts[0]+1}.0.0'
        elif version_type == 'minor':
            new_version = f'{parts[0]}.{parts[1]+1}.0'
        else:
            new_version = f'{parts[0]}.{parts[1]}.{parts[2]+1}'

        print(f'Next release version is {new_version}')

        return new_version

    def create_release_markdown(self, pr_df):
        """
        Create release note markdown from PR DataFrame and
        Write to a markdown file named: `<repo name>-<release version>.md`
        """
        print('Creating release note markdown ...\n')

        # Emoji count summary markdown string
        emoji_counts = ' '.join([
            f'{idx} x{row["number"]}'
            for idx, row in pr_df.groupby('emoji').count().iterrows()
        ])
        # Category count summary markdown string
        endpoint = f'{self.base_url}/labels'
        category_counts = ' '.join([
            f'[{cat}]({endpoint}/{cat}) x{row["number"]}'
            for cat, row in pr_df.groupby('category').count().iterrows()
        ])
        # PR summary markdown string
        prs = '\n'.join(
            [f'- (#{row["number"]}) {row["title"]} - @{row["user"]}'
             for _, row in pr_df.iterrows()]
        )

        # Construct release notes markdown
        title = (
            'Kids First' + ' '.join(self.repo.split('-')).title().lstrip('Kf')
        )
        notes = f"# {title} Release {self.release_version}"
        notes += '\n\n## Features\n\n'
        notes += '### Summary\n\n'
        notes += f'Feature Emojis: {emoji_counts} \n'
        notes += f'Feature Categories: {category_counts} \n\n'
        notes += '### New features and changes\n\n'
        notes += prs

        print('#'*80)
        print(notes+'\n\n')

        # Write markdown file
        file_name = f'{self.repo}-{self.release_version}.md'
        with open(file_name, 'w') as f:
            f.write(notes)

        print(f'Saved release notes to {file_name}')

    def release_notes(self,
                      org=config.DEFAULT_GH_ORG,
                      repo=config.DEFAULT_GH_REPO,
                      version_type='minor'):
        """
        Make release notes
        """
        print('\nBegin making release notes ...')
        # Set up session
        gh_token = get_gh_token()
        self.org = org
        self.repo = repo
        self.base_url = f'{self.api}/repos/{self.org}/{self.repo}'
        self.session = requests.Session()
        self.session.headers.update({'Authorization': 'token ' + gh_token})

        # Get all PRs
        prs = self.get_prs()
        if not prs:
            print('0 PRs found. Nothing to do, exiting')
            exit(0)

        # Get tag of last release
        latest_tag = self.get_last_tag()

        # Make pull request DataFrame
        pr_df = self.make_pr_df(prs, latest_tag)

        # Generate next release version
        self.release_version = self.next_release_version(
            latest_tag['version_number'],
            version_type=version_type)

        # Create release notes
        self.create_release_markdown(pr_df)
