"""Constants defining standard git property keys.

Compatible with Spring Boot Actuator, npm-git-properties, and gradle-git-properties.
"""

KEY_GIT_BRANCH = "git.branch"
KEY_GIT_BUILD_HOST = "git.build.host"
KEY_GIT_BUILD_VERSION = "git.build.version"
KEY_GIT_BUILD_USER_NAME = "git.build.user.name"
KEY_GIT_BUILD_USER_EMAIL = "git.build.user.email"
KEY_GIT_COMMIT_ID_ABBREVIATED = "git.commit.id.abbrev"
KEY_GIT_COMMIT_ID_DESCRIBE = "git.commit.id.describe"
KEY_GIT_COMMIT_ID = "git.commit.id.full"
KEY_GIT_COMMIT_SHORT_MESSAGE = "git.commit.message.short"
KEY_GIT_COMMIT_FULL_MESSAGE = "git.commit.message.full"
KEY_GIT_COMMIT_USER_NAME = "git.commit.user.name"
KEY_GIT_COMMIT_USER_EMAIL = "git.commit.user.email"
KEY_GIT_COMMIT_TIME = "git.commit.time"
KEY_GIT_DIRTY = "git.dirty"
KEY_GIT_REMOTE_ORIGIN_URL = "git.remote.origin.url"
KEY_GIT_TAGS = "git.tags"
KEY_GIT_CLOSEST_TAG_NAME = "git.closest.tag.name"
KEY_GIT_CLOSEST_TAG_COMMIT_COUNT = "git.closest.tag.commit.count"
KEY_GIT_TOTAL_COMMIT_COUNT = "git.total.commit.count"

__all__ = [
    "KEY_GIT_BRANCH",
    "KEY_GIT_BUILD_HOST",
    "KEY_GIT_BUILD_VERSION",
    "KEY_GIT_BUILD_USER_NAME",
    "KEY_GIT_BUILD_USER_EMAIL",
    "KEY_GIT_COMMIT_ID_ABBREVIATED",
    "KEY_GIT_COMMIT_ID_DESCRIBE",
    "KEY_GIT_COMMIT_ID",
    "KEY_GIT_COMMIT_SHORT_MESSAGE",
    "KEY_GIT_COMMIT_FULL_MESSAGE",
    "KEY_GIT_COMMIT_USER_NAME",
    "KEY_GIT_COMMIT_USER_EMAIL",
    "KEY_GIT_COMMIT_TIME",
    "KEY_GIT_DIRTY",
    "KEY_GIT_REMOTE_ORIGIN_URL",
    "KEY_GIT_TAGS",
    "KEY_GIT_CLOSEST_TAG_NAME",
    "KEY_GIT_CLOSEST_TAG_COMMIT_COUNT",
    "KEY_GIT_TOTAL_COMMIT_COUNT",
]
