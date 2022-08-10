# gitsync
Syncs & configures git repositories.

## Why
We have quite a few repos on GitHub that are mirrored from our internal GitLab.
Since OSS GitLab only supports push mirroring, there is quite some potential for
things to go wrong(push to GitHub and mirroring will always fail from then on),
on top of which it is difficult to keep track if all the repos are set up correctly.
Therefore, this tool.

## Features
* Sync git branches and git tags between repos on different providers
  * Only fast-forwards can be performed for obvious reasons
  * The tool will perform a clone over HTTPS of the full repository if changes are detected

## Supported Git platforms
Currently, only GitHub and GitLab are supported, since that is what we use.

## Example configuration
```
providers:
  - name: github
    github:
      token: <github PAT>
  - name: gitlab
    gitlab:
      token: <gitlab PAT>
      url: https://git.sos.ethz.ch
repos:
  - name: kubernetes
    origin:
      provider: gitlab
      name: pkgs/kubernetes
    mirrors:
      - provider: github
        name: vsk8s/kubernetes
```

## License
Apache 2
