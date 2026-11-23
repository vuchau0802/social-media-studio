from app.repositories.posts import find_post, insert_post

class PostNotFoundError(LookupError):
    pass


def require_post(post_id: int) -> dict:
    post = find_post(post_id)

    if post is None:
        raise PostNotFoundError("Post not found.")

    return post

def create_stored_post(markdown: str) -> int:
    if not markdown.strip():
        raise ValueError("Markdown must contain text.")

    return insert_post(markdown)