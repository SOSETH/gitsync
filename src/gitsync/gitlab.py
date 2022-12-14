import gitlab
from gitlab.v4.objects import Project
from urllib.parse import urlparse
from typing import List, Set
from gitsync.api import GitProvider, GitProject
from datetime import datetime, timedelta, timezone


class GitLabProject(GitProject):
    def __init__(self, project: Project, provider):
        super().__init__()
        self.__project__ = project
        self.__provider__ = provider
        self.__branches__ = []

    def get_url_from_project(self) -> str:
        url = self.__project__.http_url_to_repo
        url = urlparse(url)
        url = url.scheme \
            + '://' \
            + self.__provider__.__client__.user.username \
            + ':' \
            + self.__provider__.__api_key__ \
            + '@' \
            + url.netloc \
            + url.path
        return url

    def get_all_branches(self) -> List[str]:
        if self.__branches__:
            return [x.name for x in self.__branches__]

        for branch in self.__project__.branches.list(iterator=True):
            self.__branch_commits__[branch.name] = branch.commit['id']
            self.__branches__.append(branch)

        return [x.name for x in self.__branches__]

    def get_active_branches(self, active_time=timedelta(days=40)) -> List[str]:
        if not self.__branches__:
            self.get_all_branches()

        branches = set([x.name for x in self.__project__.protectedbranches.list()])
        new_branches = set()

        for branch in branches:
            if '*' not in branch:
                new_branches.add(branch)
        branches = new_branches

        for branch in self.__branches__:
            last_commit = datetime.fromisoformat(branch.commit['committed_date'])
            if datetime.now(timezone.utc) - last_commit <= active_time:
                branches.add(branch.name)
            self.__branch_commits__[branch.name] = branch.commit['id']

        return list(branches)

    def get_tags(self) -> Set[str]:
        return set([x.name for x in self.__project__.tags.list(iterator=True)])

    def get_push_mirrors(self) -> List[str]:
        return [x.url for x in self.__project__.remote_mirrors.list(iterator=True)]

    def add_push_mirror(self, url: str, only_protected_branches: bool):
        self.__project__.remote_mirrors.create(
            {
                'url': url,
                'only_protected_branches': only_protected_branches,
                'enabled': True
            }
        )

    def get_pull_mirrors(self) -> List[str]:
        raise NotImplementedError

    def add_pull_mirror(self, url: str):
        raise NotImplementedError


class GitLab(GitProvider):
    def __init__(self, instance: str, api_key: str):
        super().__init__()
        self.__client__ = gitlab.Gitlab(url=instance, private_token=api_key)
        self.__client__.auth()
        self.__api_key__ = api_key

    def get_project(self, project: str) -> GitLabProject:
        return GitLabProject(self.__client__.projects.get(project), self)

    def supports_push_mirroring(self):
        return True
