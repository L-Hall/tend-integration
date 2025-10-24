"""Constants for the FlowHome integration."""

DOMAIN = "flowhome"
DEFAULT_PORT = 8080

# Attributes
ATTR_CHORE_ID = "chore_id"
ATTR_USER_ID = "user_id"
ATTR_USER_NAME = "user_name"
ATTR_POINTS = "points"
ATTR_ASSIGNED_TO = "assigned_to"
ATTR_ROOM = "room"
ATTR_FREQUENCY = "frequency"
ATTR_DIFFICULTY = "difficulty"
ATTR_LAST_COMPLETED = "last_completed"
ATTR_NEXT_DUE = "next_due"
ATTR_COMPLETED_BY = "completed_by"
ATTR_STREAK = "streak"

# Services
SERVICE_COMPLETE_CHORE = "complete_chore"
SERVICE_SKIP_CHORE = "skip_chore"
SERVICE_ASSIGN_CHORE = "assign_chore"
SERVICE_REGISTER_WEBHOOK = "register_webhook"
SERVICE_UNREGISTER_WEBHOOK = "unregister_webhook"

EVENT_WEBHOOK_RECEIVED = "flowhome_webhook_received"

CONF_USE_SSL = "use_ssl"
