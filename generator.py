import re

from profiles import PROFILES

TEMPLATES = {
    "mock_x": ("From the blog: ", " #Blog"),
    "mock_linkedin": ("From our latest article:\n\n", "\n\n#Insights"),
    "mastodon": ("Sharing an excerpt from our blog:\n\n", "\n\n#Blog"),
}


def generate_variants(markdown: str) -> list[dict]:
    source = markdown.replace("#", "").replace("!", "")
    source = re.sub(r"\s+", " ", source).strip()

    variants = []

    for platform, (prefix, suffix) in TEMPLATES.items():
        available = PROFILES[platform]["max_length"] - len(prefix) - len(suffix)
        excerpt = source[:available].rstrip()

        variants.append({
            "platform": platform,
            "text": f"{prefix}{excerpt}{suffix}",
        })

    return variants