#!/bin/sh
rm -r public/ docs/*
hugo
mv public/* docs/
git status
git add .
git commit -m "updated BY $(git config user.name) AT $(date +"%Y-%m-%d %T")"
git push -u origin master

# Backup @ Gitee
../gitee/blog/deploy.sh
