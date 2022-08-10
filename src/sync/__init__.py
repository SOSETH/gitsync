import io
import yaml
import logging as log
from src import lib


def do_sync():
    log.basicConfig(format='%(asctime)s %(message)s', level=log.INFO)

    with io.open('config.yaml') as config_file:
        config = yaml.safe_load(config_file)

        # Step 1: Init providers
        providers = {}
        for provider in config['providers']:
            name = provider['name']
            if 'github' in provider:
                providers[name] = lib.GitHub(provider['github']['token'])
            elif 'gitlab' in provider:
                providers[name] = lib.GitLab(provider['gitlab']['url'], provider['gitlab']['token'])
            else:
                raise 'Unknown provider type for provider ' + name

        # Step 2: Sync repos
        for repo in config['repos']:
            log.info('Syncing repo {}'.format(repo['name']))

            origin = providers[repo['origin']['provider']].get_project(repo['origin']['name'])
            branches = origin.get_active_branches()
            branch_commits = {x: origin.get_last_commit_on_branch(x) for x in branches}
            tags = origin.get_tags()

            mirror_refs = {}
            mirror_tags = {}
            need_sync = False
            for mirror in repo['mirrors']:
                name = mirror['provider']
                log.info('checking mirror on {}'.format(name))
                mirror_ref = providers[mirror['provider']].get_project(mirror['name'])
                mirror_refs[name] = mirror_ref
                mirror_tags[name] = mirror_ref.get_tags()

                for x in mirror_ref.get_active_branches():
                    if x not in branches:
                        log.info("Branch {} available on mirror but not on origin".format(x))
                        branches.append(x)
                        need_sync = True

                if not need_sync:
                    if mirror_tags[name] != tags:
                        log.info("Tags on mirror {} out of date".format(name))
                        need_sync = True
                    else:
                        for x in branches:
                            if mirror_ref.get_last_commit_on_branch(x) != branch_commits[x]:
                                log.info("Branch {} on mirror {} out of date".format(x, name))
                                need_sync = True

            if need_sync:
                log.info("Cloning repo")
                with lib.Git(origin.get_url_from_project()) as git_repo:
                    for mirror in repo['mirrors']:
                        name = mirror['provider']
                        log.info("Adding remote {}".format(name))
                        downstream = mirror_refs[name]
                        git_repo.add_remote(downstream.get_url_from_project(), name)

                        for x in branches:
                            upstream_commit = branch_commits[x]
                            upstream_commit_ref = git_repo.get_commit(upstream_commit)
                            downstream_commit = downstream.get_last_commit_on_branch(x)
                            downstream_commit_ref = git_repo.get_commit(downstream_commit)

                            if upstream_commit == downstream_commit:
                                continue

                            if git_repo.is_ancestor(downstream_commit_ref, upstream_commit_ref):
                                # Upstream is newer
                                log.info("Pushing origin commits to mirror")
                                git_repo.push(upstream_commit, x, name)
                            elif git_repo.is_ancestor(upstream_commit_ref, downstream_commit_ref):
                                # Downstream is newer
                                log.info("Pushing mirror commits to origin")
                                git_repo.push(downstream_commit, x, 'origin')
                            else:
                                # We have no idea. It's not a fast-forward, so we give up here.
                                log.error("Branch {} on remote {} diverged, you need to fix this manually!"
                                          .format(x, name))

                        for x in (tags - mirror_tags[name]):
                            log.info("Pushing tag {} to mirror".format(x))
                            git_repo.push_tag(x, mirror['provider'])
                        for x in (mirror_tags[name] - tags):
                            log.info("Pushing tag {} to origin".format(x))
                            git_repo.push_tag(x, 'origin')

            # Since we now have all the repos, lets see if we need to adjust any mirroring configurations
            # Should we add push mirroring to all mirrors to origin?
            if providers[repo['origin']['provider']].supports_push_mirroring():
                mirrors = origin.get_push_mirrors()
                mirrors = [lib.filter_url(x) for x in mirrors]

                for k, v in mirror_refs.items():
                    url = v.get_url_from_project()
                    filtered = lib.filter_url(url)
                    if filtered not in mirrors:
                        log.info("Adding push mirror for {} to origin".format(k))
                        origin.add_push_mirror(url, True)

            # Should we add push or pull mirroring on mirrors to/from origin?
            for k, v in mirror_refs.items():
                url = origin.get_url_from_project()
                filtered = lib.filter_url(url)

                if providers[k].supports_push_mirroring():
                    mirrors = v.get_push_mirrors()
                    mirrors = [lib.filter_url(x) for x in mirrors]
                    if filtered not in mirrors:
                        log.info("Adding push mirror for origin to {}".format(k))
                        v.add_push_mirror(url, True)
                if providers[k].supports_pull_mirroring():
                    mirrors = v.get()
                    mirrors = [lib.filter_url(x) for x in mirrors]
                    if filtered not in mirrors:
                        log.info("Adding pull mirror from origin to {}".format(k))
                        v.add_pull_mirror(url)
