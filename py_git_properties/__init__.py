"""py-git-properties: A zero-dependency Python library & CLI to extract git repository metadata.

Outputs git metadata in JSON, flat-JSON, or Spring Boot Actuator compatible
Java .properties format.
"""

from .constants import (
    KEY_GIT_BRANCH,
    KEY_GIT_BUILD_HOST,
    KEY_GIT_BUILD_USER_EMAIL,
    KEY_GIT_BUILD_USER_NAME,
    KEY_GIT_BUILD_VERSION,
    KEY_GIT_CLOSEST_TAG_COMMIT_COUNT,
    KEY_GIT_CLOSEST_TAG_NAME,
    KEY_GIT_COMMIT_FULL_MESSAGE,
    KEY_GIT_COMMIT_ID,
    KEY_GIT_COMMIT_ID_ABBREVIATED,
    KEY_GIT_COMMIT_ID_DESCRIBE,
    KEY_GIT_COMMIT_SHORT_MESSAGE,
    KEY_GIT_COMMIT_TIME,
    KEY_GIT_COMMIT_USER_EMAIL,
    KEY_GIT_COMMIT_USER_NAME,
    KEY_GIT_DIRTY,
    KEY_GIT_REMOTE_ORIGIN_URL,
    KEY_GIT_TAGS,
    KEY_GIT_TOTAL_COMMIT_COUNT,
)
from .core import (
    build_host,
    build_version,
    closest_tag_commit_count,
    closest_tag_commit_count_async,
    commit_id_abbrev,
    commit_id_abbrev_async,
    commit_id_desc_and_tags,
    commit_id_desc_and_tags_async,
    commit_id_full,
    commit_id_full_async,
    commit_user_info,
    commit_user_info_async,
    count_of_all_commits,
    count_of_all_commits_async,
    create_git_info_file,
    create_git_info_file_async,
    current_branch,
    current_branch_async,
    date_of_last_commit,
    date_of_last_commit_async,
    get_git_prop,
    get_git_prop_async,
    git_info_as_json,
    git_info_as_json_async,
    git_info_as_properties,
    git_info_as_properties_async,
    is_dirty,
    is_dirty_async,
    last_commit_msg,
    last_commit_msg_async,
    remote_url,
    remote_url_async,
)
from .cli import CliResult, main, run_cli

__version__ = "2.1.0"

# camelCase Aliases for JavaScript / npm-git-properties parity
currentBranch = current_branch
currentBranchAsync = current_branch_async
commitIdAbbrev = commit_id_abbrev
commitIdAbbrevAsync = commit_id_abbrev_async
commitIdFull = commit_id_full
commitIdFullAsync = commit_id_full_async
lastCommitMsg = last_commit_msg
lastCommitMsgAsync = last_commit_msg_async
commitUserInfo = commit_user_info
commitUserInfoAsync = commit_user_info_async
dateOfLastCommit = date_of_last_commit
dateOfLastCommitAsync = date_of_last_commit_async
isDirty = is_dirty
isDirtyAsync = is_dirty_async
remoteUrl = remote_url
remoteUrlAsync = remote_url_async
commitIdDescAndTags = commit_id_desc_and_tags
commitIdDescAndTagsAsync = commit_id_desc_and_tags_async
closestTagCommitCount = closest_tag_commit_count
closestTagCommitCountAsync = closest_tag_commit_count_async
countOfAllCommits = count_of_all_commits
countOfAllCommitsAsync = count_of_all_commits_async
buildHost = build_host
buildVersion = build_version
getGitProp = get_git_prop
getGitPropAsync = get_git_prop_async
gitInfoAsJson = git_info_as_json
gitInfoAsJsonAsync = git_info_as_json_async
gitInfoAsProperties = git_info_as_properties
gitInfoAsPropertiesAsync = git_info_as_properties_async
createGitInfoFile = create_git_info_file
createGitInfoFileAsync = create_git_info_file_async

__all__ = [
    "__version__",
    # Constants
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
    # Sync Core Functions
    "current_branch",
    "currentBranch",
    "build_host",
    "buildHost",
    "build_version",
    "buildVersion",
    "commit_id_abbrev",
    "commitIdAbbrev",
    "commit_id_full",
    "commitIdFull",
    "last_commit_msg",
    "lastCommitMsg",
    "commit_user_info",
    "commitUserInfo",
    "date_of_last_commit",
    "dateOfLastCommit",
    "is_dirty",
    "isDirty",
    "remote_url",
    "remoteUrl",
    "commit_id_desc_and_tags",
    "commitIdDescAndTags",
    "closest_tag_commit_count",
    "closestTagCommitCount",
    "count_of_all_commits",
    "countOfAllCommits",
    "get_git_prop",
    "getGitProp",
    "git_info_as_json",
    "gitInfoAsJson",
    "git_info_as_properties",
    "gitInfoAsProperties",
    "create_git_info_file",
    "createGitInfoFile",
    # Async Core Functions
    "current_branch_async",
    "currentBranchAsync",
    "commit_id_abbrev_async",
    "commitIdAbbrevAsync",
    "commit_id_full_async",
    "commitIdFullAsync",
    "last_commit_msg_async",
    "lastCommitMsgAsync",
    "commit_user_info_async",
    "commitUserInfoAsync",
    "date_of_last_commit_async",
    "dateOfLastCommitAsync",
    "is_dirty_async",
    "isDirtyAsync",
    "remote_url_async",
    "remoteUrlAsync",
    "commit_id_desc_and_tags_async",
    "commitIdDescAndTagsAsync",
    "closest_tag_commit_count_async",
    "closestTagCommitCountAsync",
    "count_of_all_commits_async",
    "countOfAllCommitsAsync",
    "get_git_prop_async",
    "getGitPropAsync",
    "git_info_as_json_async",
    "gitInfoAsJsonAsync",
    "git_info_as_properties_async",
    "gitInfoAsPropertiesAsync",
    "create_git_info_file_async",
    "createGitInfoFileAsync",
    # CLI
    "CliResult",
    "run_cli",
    "main",
]
