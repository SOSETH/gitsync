from git import Repo, Commit
import tempfile
import shutil


class Git:
    def __init__(self, origin: str):
        self.__target__ = tempfile.mkdtemp()
        self.__repo__ = Repo.clone_from(url=origin, to_path=self.__target__)

    def add_remote(self, remote: str, name: str):
        origin = self.__repo__.create_remote(name, remote)
        origin.fetch()

    def get_commit(self, rev: str) -> Commit:
        return self.__repo__.commit(rev)

    def is_ancestor(self, commit_a: Commit, commit_b: Commit) -> bool:
        return self.__repo__.is_ancestor(commit_a, commit_b)

    def push(self, commit: str, name: str, remote: str) -> bool:
        self.__repo__.create_head(name, commit)
        remote = self.__repo__.remote(remote)
        result = remote.push(name + ':' + name)
        if len(result) < 1:
            return False
        return result[0].flags & result[0].FAST_FORWARD

    def push_tag(self, tag: str, remote: str):
        remote = self.__repo__.remote(remote)
        remote.push(tag)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        shutil.rmtree(self.__target__, ignore_errors=True)
        return exc_type is None
