# ChoreTracker Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

This integration connects your ChoreTracker app with Home Assistant, enabling automation and monitoring of household chores.

## Features

- 🏠 **Auto-discovery** - Automatically finds ChoreTracker apps on your network
- 📊 **Real-time sensors** - Track points, streaks, and chore completion status
- 🔔 **Binary sensors** - Monitor overdue chores
- 🎯 **Service calls** - Complete or skip chores from automations
- 👥 **Multi-user support** - Track individual family member progress
- 🔄 **Automatic updates** - Syncs with your ChoreTracker app every 30 seconds

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots menu and select "Custom repositories"
4. Add this repository URL: `https://github.com/L-Hall/chore-tracker-integration`
5. Select "Integration" as the category
6. Click "Add"
7. Search for "ChoreTracker" and install it
8. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/chore_tracker` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "ChoreTracker"
4. Enter your ChoreTracker app details:
   - **Host**: IP address of device running ChoreTracker
   - **Port**: API port (default: 8080)
   - **API Key**: Optional, if your app requires authentication

## Required ChoreTracker App Setup

Your ChoreTracker app needs to expose an API server. Add this to your Flutter app:

```dart
// Add to your ChoreTracker app
import 'package:shelf/shelf.dart';
import 'package:shelf/shelf_io.dart' as io;

class ChoreTrackerAPIServer {
  Future<void> start() async {
    var handler = Pipeline()
        .addMiddleware(logRequests())
        .addHandler(_handleRequest);
    
    await io.serve(handler, '0.0.0.0', 8080);
  }
  
  Response _handleRequest(Request request) {
    // Implement API endpoints
    // GET /api/info
    // GET /api/chores
    // GET /api/users
    // GET /api/leaderboard
    // POST /api/chores/{id}/complete
    // POST /api/chores/{id}/skip
  }
}
```

## Entities Created

### Sensors
- `sensor.choretracker_[user]_points` - User's total points
- `sensor.choretracker_household_points` - Total household points
- `sensor.choretracker_chore_[name]` - Last completion time for each chore

### Binary Sensors
- `binary_sensor.choretracker_[chore]_overdue` - True when chore is overdue

### Buttons
- `button.choretracker_complete_[chore]` - Press to mark chore as complete

## Services

### choretracker.complete_chore
Mark a chore as completed.

| Parameter | Description |
|-----------|-------------|
| chore_id | ID of the chore |
| user_id | ID of the user completing it |

### choretracker.skip_chore
Skip a chore with a reason.

| Parameter | Description |
|-----------|-------------|
| chore_id | ID of the chore |
| user_id | ID of the user skipping it |
| reason | Reason for skipping |

## Automation Examples

### Reward kids when they complete chores
```yaml
automation:
  - alias: "Chore Completion Reward"
    trigger:
      - platform: state
        entity_id: sensor.choretracker_riley_points
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state|int > trigger.from_state.state|int }}"
    action:
      - service: light.turn_on
        entity_id: light.kids_room
        data:
          brightness: 255
          effect: rainbow
```

### Notify when chores are overdue
```yaml
automation:
  - alias: "Overdue Chore Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.choretracker_dishes_overdue
        to: "on"
        for: "01:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Chore Overdue!"
          message: "The dishes haven't been done today"
```

### Complete chore via voice assistant
```yaml
script:
  complete_dishes:
    alias: "Mark Dishes as Done"
    sequence:
      - service: choretracker.complete_chore
        data:
          chore_id: "chore_dishes_123"
          user_id: "user_alex_456"
```

## Troubleshooting

### Integration not discovering app
1. Ensure ChoreTracker app API server is running
2. Check firewall allows port 8080
3. Verify devices are on same network

### Entities not updating
1. Check ChoreTracker app is running
2. Verify network connectivity
3. Check Home Assistant logs for errors

## Support

- [Report Issues](https://github.com/L-Hall/chore-tracker-integration/issues)
- [ChoreTracker App Repository](https://github.com/L-Hall/chore-tracker)

## License

MIT License - See LICENSE file for details