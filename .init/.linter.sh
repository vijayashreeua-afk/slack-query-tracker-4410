#!/bin/bash
cd /home/kavia/workspace/code-generation/slack-query-tracker-4410/react_frontend
npm run build
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
   exit 1
fi

