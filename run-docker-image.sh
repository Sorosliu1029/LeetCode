#!/bin/zsh
docker run -it --rm \
      --name leet \
      --publish 8888:8888 \
      --volume "$PWD":/home/jovyan \
      --user "$(id -u)" \
      --group-add users \
      ghcr.io/sorosliu1029/leetcode:latest \
      start-notebook.py --IdentityProvider.token=''

      # --env DOCKER_STACKS_JUPYTER_CMD=notebook \