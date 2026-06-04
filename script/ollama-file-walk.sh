#!/bin/bash

# script to walk through the directory and aggregate for Ollama
VERBOSE=1
# prepare arugments: ollama url and ollama model
PATH_DIR=$1

set -e

if [ -v OLLAMA_API_URL ]; then
    echo "OLLAMA URL is set"
else 
    echo "OLLAMA URL is not set, fall back to default value"
    OLLAMA_API_URL="http://localhost:11434"
    # verify
    # echo $OLLAMA_API_URL
fi

if [ -v OLLAMA_DEFAULT_MODEL ]; then
    echo "OLLAMA MODEL is set"
else
    echo "OLLAMA MODEL is not set, fall back to default value"
    OLLAMA_DEFAULT_MODEL="gemma4"
    # verify
    echo $OLLAMA_DEFAULT_MODEL
fi

# check the status of OLLAMA, otherwise, start it
OLLAMA_STATUS=$(curl -s $OLLAMA_API_URL)

if [ -z OLLAMA_STATUS ]; then
    echo "OLLAMA is not started yet, starting the ollama"
else
    echo "OLLAMA is running"
fi

if [ -z PATH_DIR ]; then
    echo "Must set the PATH directory to work"
    echo "Instruction ollama-file-walk.sh path/to/search"
    exit 1
fi

echo "$PATH_DIR"

find $(pwd) -type f -print0 | while IFS= read -r -d '' file; do
    echo "Processing: $file"
done
