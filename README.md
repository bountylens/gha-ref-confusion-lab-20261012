# Controlled GitHub Actions persistent-runner PoC

This repository contains an owned, end-to-end reproduction of a CI trust-boundary failure relevant to `facebookresearch/faiss`:

> An approved external-fork pull request executes attacker-controlled code on a persistent self-hosted runner. If that code can preserve a durable executable path or neutralize an in-guest cleanup hook, a later trusted job on the same runner can expose its write-scoped checkout token to the persisted code.

No code was executed on Meta infrastructure, no Meta credential was accessed, and no plaintext credential is stored here. The reproduction used an ephemeral AWS instance and repositories controlled by the researcher.

## Controlled result

The positive test used the same fixed self-hosted runner for an external-fork PR followed by a trusted `main` push:

1. [PR #5](https://github.com/bountylens/gha-ref-confusion-lab-20261012/pull/5) supplied the controlled persistence files from the public fork branch [`persistence-hook-bypass`](https://github.com/SoufElhabti/gha-ref-confusion-lab-20261012/tree/persistence-hook-bypass).
2. [PR run 38190469394](https://github.com/bountylens/gha-ref-confusion-lab-20261012/actions/runs/38190469394) installed a controlled `/usr/local/bin/git` wrapper and replaced the test-owned completion hook with a benign no-op.
3. [Trusted push run 38190498770](https://github.com/bountylens/gha-ref-confusion-lab-20261012/actions/runs/38190498770) ran on the same runner, `controlled-aws-i-098012f60d1c569c5`.
4. `actions/checkout` selected the persisted Git wrapper. The wrapper read checkout's Basic credential only after checkout stored it in the local Git configuration.
5. The wrapper retained only the token's SHA-256 and used the live token once to create `refs/heads/controlled-persistence-38190498770` at trusted SHA `1edd382860a2292789d1af1a593bfa21dc5ee87a`. GitHub returned HTTP `201`.
6. The controlled branch, runner, instance, security group, and canary secrets were removed after evidence collection.

The sanitized proof is [`evidence/owned-proof.json`](evidence/owned-proof.json). It contains hashes, runner identity, the controlled ref name, and the API status; it contains no plaintext token or secret.

## Negative control

[PR #4](https://github.com/bountylens/gha-ref-confusion-lab-20261012/pull/4) used the public fork branch [`persistence-control`](https://github.com/SoufElhabti/gha-ref-confusion-lab-20261012/tree/persistence-control). Its administrator completion hook removed the wrapper and `/opt/controlled` state.

- [PR control run 38190046353](https://github.com/bountylens/gha-ref-confusion-lab-20261012/actions/runs/38190046353)
- [Trusted control run 38190077017](https://github.com/bountylens/gha-ref-confusion-lab-20261012/actions/runs/38190077017)

The trusted control failed because the proof file did not exist. This establishes that an effective cleanup or genuinely ephemeral runner breaks this specific chain.

## Correspondence to `facebookresearch/faiss`

The target was not tested. Public target evidence establishes the corresponding boundary:

- [`build.yml`](https://github.com/facebookresearch/faiss/blob/cec5702b0b1c31f242b9d35d5f193b0d80ccd9dc/.github/workflows/build.yml) runs the same build family for pull requests and trusted `main` pushes.
- [`build-pull-request.yml`](https://github.com/facebookresearch/faiss/blob/cec5702b0b1c31f242b9d35d5f193b0d80ccd9dc/.github/workflows/build-pull-request.yml#L91-L124) checks out and executes repository-local build code on `faiss-aws-m7i.large` runners.
- [External-fork job 113657498307](https://github.com/facebookresearch/faiss/actions/runs/37842948398/job/113657498307) ran PR-controlled code on runner ID `106`, runner `faiss-aws-m7i.large-07`, machine `ip-172-31-37-187`. It successfully ran `sudo apt-get`, and its log identifies `backup.sh` and `cleanup_job.sh` runner hooks.
- [Trusted-main job 113968874287](https://github.com/facebookresearch/faiss/actions/runs/37971869287/job/113968874287) began five seconds later on the exact same runner ID, name, and machine. Its log advertises `Contents: write`, many other write permissions, `Secret source: Actions`, and checkout with `persist-credentials: true`.
- The repository's [build action](https://github.com/facebookresearch/faiss/blob/cec5702b0b1c31f242b9d35d5f193b0d80ccd9dc/.github/actions/build_cmake/action.yml#L58-L72) explicitly notes that a Conda prefix survives on a self-hosted runner, corroborating retained user state.

Target exploitation is therefore conditional on the unresolved target-specific gate: whether `cleanup_job.sh`, the sudo policy, or another durable executable path permits attacker-controlled state to survive. The public evidence does not disclose the cleanup script's contents, filesystem ownership, or full sudoers rule.

## Impact demonstrated in the owned repository

The owned reproduction demonstrates that persisted PR code can intercept a later trusted checkout credential and use it for an authenticated repository write. On a production repository, the practical impact depends on token permissions and branch/environment protections, but can include unauthorized repository refs or changes, CI persistence, and compromise of later release or package workflows.

## Relevant files

- [Trusted/PR workflow](.github/workflows/persistent-runner.yml)
- [Positive PR installer](https://github.com/SoufElhabti/gha-ref-confusion-lab-20261012/blob/persistence-hook-bypass/install_persistence.sh)
- [Controlled Git wrapper](https://github.com/SoufElhabti/gha-ref-confusion-lab-20261012/blob/persistence-hook-bypass/controlled_git_wrapper.sh)
- [Sanitized capture and repository-write proof](https://github.com/SoufElhabti/gha-ref-confusion-lab-20261012/blob/persistence-hook-bypass/controlled_capture.py)
- [Effective cleanup control](https://github.com/SoufElhabti/gha-ref-confusion-lab-20261012/blob/persistence-control/controlled_cleanup_strong.sh)

GitHub's own guidance warns that persistent self-hosted runners can be compromised by untrusted workflow code and should almost never be used for public repositories: <https://docs.github.com/en/actions/reference/security/secure-use>.
