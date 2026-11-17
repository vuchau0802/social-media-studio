# Social Media Studio Design

## Goal
Turn one stored blog post into platform-specific drafts. A person
approves each draft before a worker can publish it.

## Platforms
- Mock X: concise, up to 280 characters and 2 hashtags.
- Mock LinkedIn: professional, up to 600 characters and 3 hashtags.
- Mastodon: conversational, up to 400 characters and 3 hashtags.

## Data
- posts: the original article and its source URL, if provided.
- variants: platform, text, and review status.
- publish_jobs: approved variant, UTC publish time, and idempotency key.
- publish_attempts: timestamp, outcome, and post link when available.
- mock_publications: stored posts for Mock X and Mock LinkedIn previews.

## API
- POST /posts — save an article from Markdown or a URL.
- POST /posts/{id}/variants — generate drafts from the stored article.
- Edit, approve, or reject a draft.
- POST /variants/{id}/schedule — schedule an approved variant.
- GET /publish-history — show publishing attempts and results.

## Publishing
A background worker picks up due jobs. Each adapter implements
publish(text, idempotency_key). A retry reuses the same key.

## Non-goal
Analytics and engagement tracking.