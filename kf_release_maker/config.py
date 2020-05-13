"""
Default config values for release maker
"""

DEFAULT_GH_API = "https://api.github.com"
GH_TOKEN_VAR = "GH_TOKEN"
RELEASE_EMOJIS = "🏷🔖"
EMOJI_CATEGORIES = {
    "Additions": {"✨", "🎉", "📈", "➕", "🌐", "🔀", "🔊"},
    "Documentation": {"💡", "📝"},
    "Removals": {"🔥", "➖", "⏪", "🔇", "🗑"},
    "Fixes": {
        "🐛",
        "🚑",
        "🔒",
        "🍎",
        "🐧",
        "🏁",
        "🤖",
        "🍏",
        "🚨",
        "✏️",
        "👽",
        "👌",
        "♿️",
        "💬",
        "🚸",
        "🥅",
    },
    "Ops": {
        "🚀",
        "💚",
        "⬇️",
        "⬆️",
        "📌",
        "👷",
        "🐳",
        "📦",
        "👥",
        "🙈",
        "📸",
        "☸️",
        "🌱",
        "🚩",
    },
}
OTHER_CATEGORY = "Other Changes"
