from typing import List, Set

from gitsync.api import GitProvider, GitProject
from github import Github, Repository
from urllib.parse import urlparse
from datetime import datetime, timedelta


class GitHubProject(GitProject):
    def __init__(self, project: Repository, provider):
        super().__init__()
        self.__project__ = project
        self.__provider__ = provider
        self.__branches__ = []

    def get_url_from_project(self) -> str:
        url = self.__project__.clone_url
        url = urlparse(url)
        url = url.scheme\
            + '://'\
            + self.__provider__.__client__.get_user().login\
            + ':' \
            + self.__provider__.__api_key__ \
            + '@' \
            + url.netloc \
            + url.path
        return url

    def get_all_branches(self) -> List[str]:
        if self.__branches__:
            return [x.name for x in self.__branches__]

        for branch in self.__project__.get_branches():
            self.__branch_commits__[branch.name] = branch.commit.sha
            self.__branches__.append(branch)

        return [x.name for x in self.__branches__]

    def get_active_branches(self, active_time=timedelta(days=40)) -> List[str]:
        if not self.__branches__:
            self.get_all_branches()

        branches = set()

        for branch in self.__branches__:
            last_commit = branch.commit.commit.committer.date
            if datetime.now() - last_commit <= active_time:
                branches.add(branch.name)
            elif branch.protected:
                branches.add(branch.name)
            elif branch.name == self.__project__.default_branch:
                branches.add(branch.name)

        return list(branches)

    def get_tags(self) -> Set[str]:
        return set([x.name for x in self.__project__.get_tags()])

    def get_pull_mirrors(self) -> List[str]:
        raise NotImplementedError

    def add_pull_mirror(self, url: str):
        raise NotImplementedError

    def get_push_mirrors(self) -> List[str]:
        raise NotImplementedError

    def add_push_mirror(self, url: str, only_protected_branches: bool):
        raise NotImplementedError


class GitHub(GitProvider):
    def __init__(self, api_key: str):
        super().__init__()
        self.__client__ = Github(api_key)
        self.__api_key__ = api_key

    def get_project(self, project: str) -> GitHubProject:
        return GitHubProject(self.__client__.get_repo(project), self)
