from datetime import timedelta
from typing import List, Set


class GitProvider:
    def __init__(self):
        pass

    def get_project(self, project: str):
        pass

    def supports_push_mirroring(self) -> bool:
        return False

    def supports_pull_mirroring(self) -> bool:
        return False


class GitProject:
    def __init__(self):
        self.__branch_commits__ = {}

    def get_last_commit_on_branch(self, branch_name: str) -> str:
        return self.__branch_commits__[branch_name]

    def get_url_from_project(self) -> str:
        pass

    def get_active_branches(self, active_time=timedelta(days=40)) -> List[str]:
        pass

    def get_tags(self) -> Set[str]:
        pass

    def get_push_mirrors(self) -> List[str]:
        pass

    def add_push_mirror(self, url: str, only_protected_branches: bool):
        pass

    def get_pull_mirrors(self) -> List[str]:
        pass

    def add_pull_mirror(self, url: str):
        pass
