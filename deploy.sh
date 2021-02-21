#!/bin/sh
rm -r public/ docs/*
hugo -d="docs"
git add .
git commit -m "updated BY $(git config user.name) AT $(date +"%Y-%m-%d %T")"
git push -u origin master
