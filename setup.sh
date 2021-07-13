#!/usr/local/bin/bash

pushd $(dirname "$BASH_SOURCE") > /dev/null
CONF_LOC='./config.json'
file_prefix_line=$(grep 'filename_prefix' $CONF_LOC | head -n 1)

if [[ $file_prefix_line =~ filename_prefix.*\"([[:alnum:]]+)\" ]]; then
  file_prefix=${BASH_REMATCH[1]}
else
  echo 'Filename Prefix not found'
fi

if [[ ! -f "./__pycache__/$file_prefix/episodes.json" ]]; then
  pushd __pycache__ > /dev/null
  mkdir $file_prefix
  touch $file_prefix/episodes.json
  echo 'Copy response to episodes.json and start again'
  popd > /dev/null
  exit 0
fi

python3 main.py
popd > /dev/null