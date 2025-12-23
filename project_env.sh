#!/bin/bash
# Project Aquarium environment

export PROJECT_DIR="$HOME/ProjectAquarium"
export HISTFILE="$PROJECT_DIR/.bash_history"   # project-only history
shopt -s histappend                             # append, don't overwrite
PROMPT_COMMAND='history -a; history -c; history -r'  # save & reload continuously

# Function to get current Git branch (if any)
git_branch() {
  branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
  if [ -n "$branch" ]; then
    echo "($branch)"
  fi
}

# Colors
GREEN="\[\e[32m\]"
BLUE="\[\e[34m\]"
PURPLE="\[\e[35m\]"
RESET="\[\e[0m\]"

# change prompt to show project
export PS1="${GREEN}(Aquarium)${RESET} \u@\h:${BLUE}\w${RESET} ${PURPLE}\$(git_branch)${RESET}\$ "
