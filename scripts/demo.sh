#!/usr/bin/env bash
set -e

echo "$ context-hygiene demo: cleaning a messy conversation"
echo "$"
echo "$ First, let's see how messy this conversation is..."
echo "$ ctx-hygiene score tests/fixtures/generic_conversation.md"
ctx-hygiene score tests/fixtures/generic_conversation.md
echo ""
echo "$ Now let's run a full audit to see all the problems..."
echo "$ ctx-hygiene audit tests/fixtures/generic_conversation.md"
ctx-hygiene audit tests/fixtures/generic_conversation.md
echo ""
echo "$ Let's preview what cleaning would remove..."
echo "$ ctx-hygiene clean tests/fixtures/generic_conversation.md --dry-run"
ctx-hygiene clean tests/fixtures/generic_conversation.md --dry-run
echo ""
echo "$ Apply the cleaning..."
echo "$ ctx-hygiene clean tests/fixtures/generic_conversation.md --apply"
ctx-hygiene clean tests/fixtures/generic_conversation.md --apply
echo ""
echo "$ Finally, score the cleaned file..."
echo "$ ctx-hygiene score tests/fixtures/generic_conversation.cleaned.md"
ctx-hygiene score tests/fixtures/generic_conversation.cleaned.md
