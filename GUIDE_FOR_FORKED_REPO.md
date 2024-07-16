## Set up Github Token

1. Go to [https://github.com/settings/tokens](https://github.com/settings/tokens) and "Generate new token (classic)" with `public_repo` scope.
2. Go to your forked repo and create a new `Repository secrets` `GH_TOKEN` with value is the token in step 1

## Get latest updates from this repo

The Github action bot will overwrite the latest commit multiple times so it is not easy to rebase. Below are the steps to merge commits from this repo.

Notice: I assume that `git commit -a` will add all binary conflicts for images directory.

```
git remote add upstream https://github.com/quanhua92/stock-investment
git fetch upstream

git merge upstream/main
git commit -a
```
