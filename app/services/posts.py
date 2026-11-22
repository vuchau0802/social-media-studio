from app.repositories.posts import find_post


class PostNotFoundError(LookupError):
    pass


def require_post(post_id: int) -> dict:
    post = find_post(post_id)

    if post is None:
        raise PostNotFoundError("Post not found.")

    return post