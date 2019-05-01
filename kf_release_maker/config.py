"""
Default config values for release maker
"""


DEFAULT_GH_ORG = 'kids-first'
DEFAULT_GH_REPO = 'kf-release-maker'
DEFAULT_GH_API = 'http://api.github.com'
GH_TOKEN_VAR = 'GH_TOKEN'
RELEASE_EMOJI = '🏷'
EMOJI_NOT_FOUND = '?'
EMOJI_CATEGORIES = {
    '✨': 'feature',
    '♻️': 'refactor',
    '📝': 'documentation',
    '🐛': 'bug',
    '👷': 'devops',
    '🐳': 'devops',
    'default': 'other'
}
VALID_VERSION_TYPES = {'major', 'minor', 'patch'}
