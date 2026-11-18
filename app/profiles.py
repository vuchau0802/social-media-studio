import re

PROFILES = {
    "mock_x": {
        "max_length": 280,
        "max_hashtags": 2,
        "max_exclamations": 1,
    },
    "mock_linkedin": {
        "max_length": 600,
        "max_hashtags": 3,
        "max_exclamations": 0,
    },
    "mastodon": {
        "max_length": 400,
        "max_hashtags": 3,
        "max_exclamations": 2,
    },
}


def validate_variant(platform: str, text: str) -> list[str]:
    if platform not in PROFILES:
        return ["Unknown platform."]

    profile = PROFILES[platform]
    errors = []

    if not text.strip():
        errors.append("Text must contain content.")

    if len(text) > profile["max_length"]:
        errors.append(
            f"Text exceeds {profile['max_length']} characters."
        )

    hashtags = re.findall(r"(?<!\w)#\w+", text)
    if len(hashtags) > profile["max_hashtags"]:
        errors.append(
            f"Text exceeds {profile['max_hashtags']} hashtags."
        )

    if text.count("!") > profile["max_exclamations"]:
        errors.append(
            f"Tone rule allows at most "
            f"{profile['max_exclamations']} exclamation marks."
        )

    return errors