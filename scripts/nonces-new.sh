#!/usr/bin/env bash

TOKEN=$(jq -r  .access_token ~/.agave/current)
BASE_URL=$(jq -r  .baseurl ~/.agave/current)

if [ -z "$ACTOR_ID" ];
then
    ACTOR_ID=$(cat .ACTOR_ID)
fi

curl -XPOST -sk -H "Authorization: Bearer $TOKEN" "${BASE_URL}/actors/v2/${ACTOR_ID}/nonces" | jq -r '.result | [ .id, .maxUses, .remainingUses, .level] | @csv' | column -t -s, | tr -d '"'

