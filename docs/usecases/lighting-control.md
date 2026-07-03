# Use Case: Lighting Control

## Intent

Manual control of the theater's Philips Hue lighting from the unified interface, complementing (not replacing) the existing play-triggered dimming automation and the lighting control already present in Roomie.

## Behavior

1. Present a small set of one-tap scene buttons (for example, Movie, Bright, Off) defined in `config/devices.yaml`.
2. Present a master brightness slider for the theater room/group.
3. Present a group on/off toggle.
4. Reflect current group state (on/off and level) read from the Hue bridge.

## Relationship to Existing Automation

- The user already dims Hue when Plex begins playback via an *arr app or webhook. That automation remains the source of truth for play-driven dimming.
- This use case provides manual override and quick scene recall. It must not disable or duplicate the play-triggered automation.

## Adapter

- Uses the Philips Hue adapter (`docs/devices/philips-hue.md`) via the local bridge API. Scenes are referenced by scene id/resource from config.

## Progress and Feedback

- Lighting actions are fast and synchronous; no multi-step progress checklist is needed. Reflect the resulting state in the panel after each action.
