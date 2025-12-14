# 🏠 Tend for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/L-Hall/tend-integration.svg)](https://github.com/L-Hall/tend-integration/releases)
[![License](https://img.shields.io/github/license/L-Hall/tend-integration.svg)](LICENSE)

Turn household chores into a game! Tend brings gamification to your smart home by connecting your household chore management with Home Assistant automations.

## ✨ What is Tend?

Tend is a gamified household chore management system that helps families track and complete household tasks through points, streaks, and friendly competition. This integration connects your Tend app with Home Assistant, enabling powerful automations and monitoring.

### Key Features

- 🎯 **Track chore completion** with real-time sensors
- 🏆 **Monitor points and streaks** for family members
- 🔔 **Get alerts** when chores are overdue
- 🤖 **Automate rewards** based on chore completion
- 📊 **View household statistics** in your dashboard
- 🎮 **Control chores** through voice assistants

---

## 📦 Installation Guide

### Method 1: Install via HACS (Easiest) 🎉

**Prerequisites:**
- Home Assistant 2024.1.0 or newer
- [HACS](https://hacs.xyz/) installed and configured

**Step-by-step:**

1. **Open HACS in Home Assistant**
   - Navigate to your Home Assistant sidebar
   - Click on "HACS"

2. **Add Custom Repository**
   - Click the 3-dot menu (⋮) in the top right
   - Select "Custom repositories"
   
3. **Add Tend Repository**
   - Repository URL: `https://github.com/L-Hall/tend-integration`
   - Category: Select "Integration"
   - Click "Add"

4. **Install Tend**
   - Go back to HACS main page
   - Click "+ Explore & Download Repositories"
   - Search for "Tend"
   - Click on Tend
   - Click "Download" button
   - Select the latest version
   - Click "Download" again

5. **Restart Home Assistant**
   - Go to Settings → System → Restart
   - Click "Restart Home Assistant"

### Method 2: Manual Installation 🛠️

**Step-by-step:**

1. **Download the Integration**
   ```bash
   # Option A: Using git
   cd /config
   git clone https://github.com/L-Hall/tend-integration.git temp_tend
   cp -r temp_tend/custom_components/flowhome custom_components/
   rm -rf temp_tend
   
   # Option B: Download ZIP
   # 1. Go to https://github.com/L-Hall/tend-integration
   # 2. Click "Code" → "Download ZIP"
   # 3. Extract the ZIP file
   # 4. Copy the 'custom_components/flowhome' folder to your Home Assistant 'custom_components' directory
   ```

2. **Verify Installation**
   - Your folder structure should look like:
   ```
   /config
   └── custom_components
       └── flowhome
           ├── __init__.py
           ├── manifest.json
           ├── config_flow.py
           └── ... (other files)
   ```

3. **Restart Home Assistant**
   - Go to Settings → System → Restart
   - Click "Restart Home Assistant"

---

## 🚀 Configuration

### Adding the Integration

1. **Navigate to Integrations**
   - Go to Settings → Devices & Services
   - Click "+ Add Integration"

2. **Search for Tend**
   - Type "Tend" in the search box
   - Click on "Tend" when it appears

3. **Configure Connection**
   
   You'll see a configuration dialog. Enter:
   
   - **Host**: The Tend API endpoint
     - Example: `https://flow-api-service-87497786761.europe-west1.run.app`
   
   - **Port**: `443` (HTTPS)
     - Change only if you have a custom endpoint/port
   
   - **API Key**: (Optional) 
     - Leave blank unless you've set up authentication in the app

4. **Click Submit**
   - The integration will connect to your Tend app
   - If successful, you'll see "Success!" message

### Auto-Discovery 🔍

If your Tend app is running on the same network, Home Assistant might automatically discover it. If you use the hosted endpoint (`flow-api-service-87497786761.europe-west1.run.app`), add it manually with port 443.

1. Check the "Discovered" section in Settings → Devices & Services
2. If Tend appears, click "Configure"
3. Confirm the details and click "Submit"

---

## 📱 Tend App Setup

**Important**: Your Tend app needs to have its API server enabled.

### Enable API Server in Tend App

1. Open the Tend app
2. Go to Settings → Integrations
3. Toggle "Enable Home Assistant Integration" ON
4. Note the displayed IP address and port
5. (Optional) Set an API key for security

### Verify Connection

Test that the API is accessible:
```bash
curl https://flow-api-service-87497786761.europe-west1.run.app/api/info
```

You should see a JSON response with app information.

---

## 🎛️ Available Entities

Once configured, Tend creates these entities in Home Assistant:

### Sensors 📊
- `sensor.flowhome_[name]_points` - Individual user points
- `sensor.flowhome_household_points` - Total household points
- `sensor.flowhome_[chore]_last_completed` - When chore was last done

### Binary Sensors 🔴🟢
- `binary_sensor.flowhome_[chore]_overdue` - Is the chore overdue?

### Buttons 🔘
- `button.flowhome_complete_[chore]` - Mark chore as complete

### Services 🔧
- `flowhome.complete_chore` - Complete a chore programmatically
- `flowhome.skip_chore` - Skip a chore with reason

---

## 🤖 Automation Examples

### Example 1: Reward Kids When They Do Chores
```yaml
automation:
  - alias: "Chore Completion Celebration"
    trigger:
      - platform: state
        entity_id: sensor.flowhome_riley_points
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state|int > trigger.from_state.state|int }}"
    action:
      - service: light.turn_on
        target:
          entity_id: light.kids_room
        data:
          effect: "rainbow"
          brightness: 255
      - service: notify.alexa_media
        data:
          target: media_player.kids_echo
          message: "Great job completing your chore! You earned {{ trigger.to_state.state|int - trigger.from_state.state|int }} points!"
```

### Example 2: Morning Chore Reminder
```yaml
automation:
  - alias: "Morning Chore Check"
    trigger:
      - platform: time
        at: "08:00:00"
    condition:
      - condition: state
        entity_id: binary_sensor.flowhome_make_bed_overdue
        state: "on"
    action:
      - service: notify.mobile_app_rileys_phone
        data:
          title: "🛏️ Morning Reminder"
          message: "Don't forget to make your bed!"
          data:
            actions:
              - action: "COMPLETE_CHORE"
                title: "Mark as Done"
```

### Example 3: Weekly Leaderboard Announcement
```yaml
automation:
  - alias: "Sunday Leaderboard"
    trigger:
      - platform: time
        at: "19:00:00"
    condition:
      - condition: time
        weekday: sun
    action:
      - service: notify.alexa_media_everywhere
        data:
          message: >
            This week's chore champion is 
            {% set users = ['sensor.flowhome_alex_points', 'sensor.flowhome_riley_points', 'sensor.flowhome_sam_points'] %}
            {% set ns = namespace(max_points=0, winner='') %}
            {% for user in users %}
              {% if states(user)|int > ns.max_points %}
                {% set ns.max_points = states(user)|int %}
                {% set ns.winner = user.split('_')[2] %}
              {% endif %}
            {% endfor %}
            {{ ns.winner }} with {{ ns.max_points }} points! Great job!
```

---

## 🎮 Dashboard Cards

### Chore Status Card
```yaml
type: entities
title: Chore Status
entities:
  - entity: binary_sensor.flowhome_dishes_overdue
    name: Dishes
    icon: mdi:dish
  - entity: binary_sensor.flowhome_vacuum_overdue
    name: Vacuum
    icon: mdi:robot-vacuum
  - entity: binary_sensor.flowhome_laundry_overdue
    name: Laundry
    icon: mdi:washing-machine
```

### Family Leaderboard
```yaml
type: custom:bar-card
title: Family Points
entities:
  - entity: sensor.flowhome_alex_points
    name: Alex
    color: '#3498db'
  - entity: sensor.flowhome_riley_points
    name: Riley
    color: '#2ecc71'
  - entity: sensor.flowhome_sam_points
    name: Sam
    color: '#e74c3c'
```

---

## 🔍 Troubleshooting

### Integration Not Found After Installation

1. **Check installation path**: Ensure files are in `/config/custom_components/flowhome/`
2. **Check file permissions**: Files should be readable by Home Assistant
3. **Clear browser cache**: Ctrl+F5 or Cmd+Shift+R
4. **Check logs**: Settings → System → Logs for any error messages

### Can't Connect to Tend App

1. **Verify network**: Ensure both devices are on the same network
2. **Check firewall**: Port 443 must be open outbound from Home Assistant
3. **Test connection**: 
   ```bash
   curl https://flow-api-service-87497786761.europe-west1.run.app/api/info
   ```
4. **Check app settings**: Ensure API server is enabled in the Tend app

### Entities Not Updating

1. **Check Tend app**: Ensure it's running and not in sleep mode
2. **Reload integration**: Settings → Devices & Services → Tend → ⋮ → Reload
3. **Check update interval**: Default is 30 seconds
4. **Review logs**: Look for connection errors in Home Assistant logs

### Common Error Messages

- **"Failed to connect"**: Check IP address and port
- **"Invalid authentication"**: Verify API key if set
- **"No data received"**: Ensure Tend app is running
- **"Already configured"**: Remove existing configuration first

---

## 📞 Support

### Getting Help

1. **Check the Wiki**: [GitHub Wiki](https://github.com/L-Hall/tend-integration/wiki)
2. **Search Issues**: [Existing Issues](https://github.com/L-Hall/tend-integration/issues)
3. **Community Forum**: [Home Assistant Community](https://community.home-assistant.io/)
4. **Report a Bug**: [Create New Issue](https://github.com/L-Hall/tend-integration/issues/new)

### Providing Feedback

We love to hear from users! Share your:
- Feature requests
- Automation ideas
- Success stories
- Bug reports

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) first.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/L-Hall/tend-integration.git
cd tend-integration

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements_dev.txt

# Run tests
pytest
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Home Assistant community for the amazing platform
- HACS team for simplifying custom integration distribution
- All contributors and testers who help improve Tend

---

## 🗺️ Roadmap

- [ ] Voice assistant integration improvements
- [ ] More detailed statistics sensors
- [ ] Chore templates and scheduling
- [ ] Multi-household support
- [ ] Energy monitoring for chore-related appliances
- [ ] AI-powered chore suggestions

---

Made with ❤️ for the Home Assistant community
