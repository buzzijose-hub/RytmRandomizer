# State Capture Roadmap

## Current State

The RytmRandomizer does not currently perform true hardware-state capture.

Current behavior:

- Load known software anchors
- Mutate known anchors
- Track values the software sends
- Return to known anchors

Not yet built:

- Read current hardware kit/sound from the Rytm
- Capture every current pad parameter automatically
- Mutate around an arbitrary manually-created hardware state

## Future Capture System

Desired features:

- Soft capture
- True hardware capture
- Captured anchors
- Commit captured state as anchor
- Return to captured anchor
- Undo
- Redo
- A/B compare
- Mutation history
- Favorites
- Live-safe capture workflow

## Soft Capture

Soft capture stores what the software already knows.

This is easier and should come first.

## True Hardware Capture

True hardware capture reads the actual current machine state, likely through SysEx request/dump parsing.

This is a larger technical feature and should come later.

## Anchor Rule

Validated anchors remain permanent.

Captured anchors are additional temporary or saved anchors.

Capture does not replace load anchors.
