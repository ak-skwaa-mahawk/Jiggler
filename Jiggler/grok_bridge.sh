#!/bin/bash

if [ -z "$XAI_API_KEY" ]; then
    echo "❌ Error: \$XAI_API_KEY environment variable is empty."
    exit 1
fi

MODEL="grok-build-0.1"
API_URL="https://api.x.ai/v1/chat/completions"

echo "================================================================="
echo "🛰️  TORDIAL-GS -> xAI COGNITIVE BRIDGE V2 ACTIVE"
echo "================================================================="

while true; do
    echo -e "\n🤖 Enter Prompt (or type 'exit' to quit):"
    read -r USER_PROMPT
    
    if [ "$USER_PROMPT" = "exit" ] || [ -z "$USER_PROMPT" ]; then
        echo "🔌 Closing cognitive link..."
        break
    fi

    echo "📄 Optional: Enter filename context (or hit Enter to skip):"
    read -r FILE_CONTEXT
    
    FULL_PAYLOAD="$USER_PROMPT"
    if [ -f "$FILE_CONTEXT" ]; then
        echo "📎 Injecting $FILE_CONTEXT safely into payload map..."
        FILE_CONTENT=$(cat "$FILE_CONTEXT")
        FULL_PAYLOAD="$USER_PROMPT"$'\n\n'"--- CONTEXT FILE: $FILE_CONTEXT ---"$'\n'"$FILE_CONTENT"
    fi

    echo "⚡ Dispatching sanitized JSON array downstream..."
    
    # Let jq build a perfectly validated, binary-safe JSON payload structure
    JSON_PAYLOAD=$(jq -n \
      --arg model "$MODEL" \
      --arg prompt "$FULL_PAYLOAD" \
      '{model: $model, messages: [{role: "user", content: $prompt}], stream: false}')

    # Ship packet smoothly across network socket
    RESPONSE=$(curl -s -X POST "$API_URL" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $XAI_API_KEY" \
      -d "$JSON_PAYLOAD")

    # Output response cleanly via built-in jq extraction parsing rules
    if echo "$RESPONSE" | jq -e '.error' >/dev/null 2>&1; then
        echo "❌ API Gateway Error:"
        echo "$RESPONSE" | jq '.error'
    elif echo "$RESPONSE" | jq -e '.choices' >/dev/null 2>&1; then
        echo -e "\n📥 Grok Generation Response:\n--------------------------------------------------"
        echo "$RESPONSE" | jq -r '.choices[0].message.content'
        echo "--------------------------------------------------"
    else
        echo "❌ System Error: Unexpected API response format received:"
        echo "$RESPONSE"
    fi
done
