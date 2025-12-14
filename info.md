# Tend Integration

{% if installed %}

## Configuration

The integration is configured via the UI. Go to Settings → Devices & Services → Add Integration → Tend.

## Entities

This integration creates:
- **Sensors** for user points and chore completion times
- **Binary sensors** for overdue chore status
- **Buttons** to complete chores
- **Services** to complete or skip chores programmatically

{% else %}

## What is Tend?

Tend is a gamified household chore management app that helps families track and complete household tasks. This integration connects your Tend app to Home Assistant.

## Features

- Auto-discovery of Tend apps on your network
- Real-time tracking of chore completion and points
- Create automations based on chore status
- Control Tend from Home Assistant

{% endif %}

## Example Automations

See the [README](https://github.com/L-Hall/tend-integration) for automation examples.
