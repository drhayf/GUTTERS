#!/bin/bash
# Auto-activation script for GUTTERS venv
# This script is sourced by your shell profile to auto-activate the venv

# Function to auto-activate venv when in GUTTERS directory
gutters_auto_activate() {
    # Check if we're in the GUTTERS directory or subdirectory
    if [[ "$PWD" == *"/GUTTERS"* ]] || [[ "$PWD" == *"\\GUTTERS"* ]]; then
        # Find the GUTTERS root directory
        local current_dir="$PWD"
        local gutters_root=""

        # Traverse up to find .venv
        while [[ "$current_dir" != "/" ]] && [[ "$current_dir" != "" ]]; do
            if [[ -d "$current_dir/.venv" ]]; then
                gutters_root="$current_dir"
                break
            fi
            current_dir="$(dirname "$current_dir")"
        done

        # If we found the venv and it's not already activated
        if [[ -n "$gutters_root" ]] && [[ "$VIRTUAL_ENV" != "$gutters_root/.venv" ]]; then
            source "$gutters_root/.venv/Scripts/activate" 2>/dev/null || \
            source "$gutters_root/.venv/bin/activate" 2>/dev/null

            if [[ $? -eq 0 ]]; then
                echo "✓ GUTTERS venv activated: $gutters_root/.venv"
            fi
        fi
    elif [[ -n "$VIRTUAL_ENV" ]] && [[ "$VIRTUAL_ENV" == *"/GUTTERS/.venv"* ]]; then
        # We left the GUTTERS directory, deactivate
        deactivate 2>/dev/null
    fi
}

# Hook into cd command
if [[ -n "$BASH_VERSION" ]]; then
    # Bash hook
    cd() {
        builtin cd "$@"
        gutters_auto_activate
    }
    # Run on shell start
    gutters_auto_activate
elif [[ -n "$ZSH_VERSION" ]]; then
    # Zsh hook
    chpwd() {
        gutters_auto_activate
    }
    # Run on shell start
    gutters_auto_activate
fi
