# FlowHome Integration

{% if installed %}

## Configuration

The integration is configured via the UI. Go to Settings → Devices & Services → Add Integration → FlowHome.

## Entities

This integration creates:
- **Sensors** for user points and chore completion times
- **Binary sensors** for overdue chore status
- **Buttons** to complete chores
- **Services** to complete or skip chores programmatically

{% else %}

## What is FlowHome?

FlowHome is a gamified household chore management app that helps families track and complete household tasks. This integration connects your FlowHome app to Home Assistant.

## Features

- Auto-discovery of FlowHome apps on your network
- Real-time tracking of chore completion and points
- Create automations based on chore status
- Control FlowHome from Home Assistant

{% endif %}

## Example Automations

See the [README](https://github.com/L-Hall/flowhome-integration) for automation examples.