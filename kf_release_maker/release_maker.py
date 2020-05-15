import sys
from collections import defaultdict
from urllib.parse import urlencode

import emoji
import regex
from d3b_utils.requests_retry import Session

import semver
from kf_release_maker import config

MAJOR = "major"
MINOR = "minor"
PATCH = "patch"

release_pattern = r"\s*[" + config.RELEASE_EMOJIS + r"]\s*Release"
emoji_categories = {
    e: category
    for category, emoji_set in config.EMOJI_CATEGORIES.items()
    for e in emoji_set
}


def split_prefix(text, pattern):
    start = regex.search(pattern, text).start()
    return text[0:start], text[start:]


class GitHubReleaseMaker(object):
    def __init__(self, gh_api=config.DEFAULT_GH_API):
        self.api = gh_api

    def _starting_emojis(self, title):
        """
        Detect emojis at the start of a PR title (and fix malformed titles)
        """
        emojis = set()
        graphemes = regex.findall(r"\X", title)
        for i, g in enumerate(graphemes):
            if any(char in emoji.UNICODE_EMOJI for char in g):
                emojis.add(g)
            else:  # stop after first non-hit
                if g != " ":
                    # fix missing space in malformed titles
                    title = (
                        "".join(graphemes[:i]) + " " + "".join(graphemes[i:])
                    )
                break

        return (emojis or {"?"}, title)

    def _get(self, url, **request_kwargs):
        """
        If response.status_code is not 200 then exit program
        Otherwise return original response
        """
        response = self.session.get(url, **request_kwargs)
        if response.status_code != 200:
            print(f"Could not fetch {url}! Caused by: {response.text}")
            exit(1)

        return response

    def _yield_paginated(self, endpoint, query_params):
        """
        Yield from paginated endpoint
        """
        query_params.update({"page": 1, "per_page": 100})
        url = f"{endpoint}?{urlencode(query_params)}"
        items = True
        while items:
            print(f'... page {query_params["page"]} ...')
            url = f"{endpoint}?{urlencode(query_params)}"
            items = self._get(url).json()
            yield from items
            query_params["page"] += 1

    def _get_merged_prs(self, after):
        """
        Get all non-release PRs merged into master after the given time
        """
        print(f"Fetching PRs ...")
        endpoint = f"{self.base_url}/pulls"
        query_params = {"base": "master", "state": "closed"}
        prs = []
        for p in self._yield_paginated(endpoint, query_params):
            if p["merged_at"]:
                if p["merged_at"] < after:
                    break
                elif regex.search(release_pattern, p["title"]) is None:
                    prs.append(p)
        return prs

    def _get_commit_date(self, commit_url):
        """
        Get date of commit at commit_url
        """
        commit = self._get(commit_url).json()
        return commit["commit"]["committer"]["date"]

    def _get_last_tag(self):
        """
        Get latest tag and when it was committed
        """
        tags = self._get(f"{self.base_url}/tags").json()

        # Get latest commit of last tagged release
        if len(tags) > 0:
            for t in tags:
                try:
                    prefix, version = split_prefix(t["name"], r"\d")
                    # Raise on non-semver tags so we can skip them
                    semver.VersionInfo.parse(version)
                    return {
                        "name": t["name"],
                        "date": self._get_commit_date(t["commit"]["url"]),
                        "commit_sha": t["commit"]["sha"],
                    }
                except ValueError:
                    pass
        else:
            return None

    def _next_release_version(self, prev_version, release_type):
        """
        Get next release version based on prev version using semver format
        """
        parts = [int(p) for p in prev_version.split(".")]
        if release_type == MAJOR:
            new_version = f"{parts[0]+1}.0.0"
        elif release_type == MINOR:
            new_version = f"{parts[0]}.{parts[1]+1}.0"
        elif release_type == PATCH:
            new_version = f"{parts[0]}.{parts[1]}.{parts[2]+1}"
        else:
            raise ValueError(
                f"Invalid release type: {release_type}! Release type "
                f"must be one of ['{MAJOR}', '{MINOR}', '{PATCH}']!"
            )

        return new_version

    def _to_markdown(self, repo, counts, prs):
        messages = [
            "### Summary",
            "",
            "- Emojis: "
            + ", ".join(f"{k} x{v}" for k, v in counts["emojis"].items()),
            "- Categories: "
            + ", ".join(f"{k} x{v}" for k, v in counts["categories"].items()),
            "",
            "### New features and changes",
            "",
        ]

        for p in prs:
            userlink = f"[{p['user']['login']}]({p['user']['html_url']})"
            sha_link = f"[{p['merge_commit_sha'][:8]}](https://github.com/{repo}/commit/{p['merge_commit_sha']})"
            pr_link = f"[#{p['number']}]({p['html_url']})"
            messages.append(
                f"- {pr_link} - {p['title']} - {sha_link} by {userlink}"
            )

        return "\n".join(messages)

    def build_release_notes(
        self, repo, release_type, blurb=None, gh_token=None
    ):
        """
        Make release notes
        """
        print("\nBegin making release notes ...")

        # Set up session
        self.base_url = f"{self.api}/repos/{repo}"
        self.session = Session()
        if gh_token:
            self.session.headers.update({"Authorization": "token " + gh_token})

        # Get tag of last release
        print(f"Fetching latest tag ...")
        latest_tag = self._get_last_tag()

        if latest_tag:
            print(f"Latest tag: {latest_tag}")
        else:
            print(f"No tags found")
            latest_tag = {"name": "0.0.0", "date": ""}

        # Get all non-release PRs that were merged into master after the last release
        prs = self._get_merged_prs(latest_tag["date"])

        # Count the emojis and fix missing spaces in titles
        counts = {"emojis": defaultdict(int), "categories": defaultdict(int)}
        for p in prs:
            emojis, p["title"] = self._starting_emojis(p["title"].strip())
            for e in emojis:
                counts["emojis"][e] += 1
                counts["categories"][
                    emoji_categories.get(e, config.OTHER_CATEGORY)
                ] += 1

        # Update release version
        prefix, prev_version = split_prefix(latest_tag["name"], r"\d")
        version = prefix + self._next_release_version(
            prev_version, release_type=release_type
        )

        # Compose markdown
        markdown = f"## Release {version}\n\n"
        if blurb:
            markdown += f"{blurb}\n\n"
        markdown += self._to_markdown(repo, counts, prs)

        print("=" * 30 + "BEGIN RECORD" + "=" * 30)
        print(markdown)
        print("=" * 31 + "END RECORD" + "=" * 31)
        return version, markdown
