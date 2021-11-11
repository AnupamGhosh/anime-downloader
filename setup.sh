#!/usr/local/bin/bash

pushd $(dirname "$BASH_SOURCE") > /dev/null
CONF_LOC='./config.json'
# `+` was not working used `*` instead
file_prefix=$(sed -n "s/[ ]*\"filename_prefix\":[ ]*\"\([^\"]*\)\",\{0,1\}/\1/p" $CONF_LOC | head -n 1)
save_in=$(sed -n "s/[ ]*\"save_in\":[ ]*\"\([^\"]*\)\",\{0,1\}/\1/p" $CONF_LOC | head -n 1)
# save_in=$(sed -n "s/[ ]*\"save_in\":[ ]*\"\([^\"]*\)\",\{0,1\}/\1/p" $CONF_LOC | head -n 1 | sed "s/ /\\\ /")
save_in=$(sed -n "s/[ ]*\"save_in\":[ ]*\"\([^\"]*\)\",\{0,1\}/\1/p" $CONF_LOC | head -n 1 | sed "s/ /\\\ /")

if [[ ! $file_prefix || ! $save_in ]]; then
  echo "Either filename_prefix=$file_prefix save_in=$save_in is missing"
  exit 0
fi


# if [[ ! -d $save_in ]]; then
#   mkdir -p $save_in
#   echo "Directory $save_in created"
# fi

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