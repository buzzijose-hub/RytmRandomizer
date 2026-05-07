# Passive Mock Knowledge Checkpoint

## 1. Purpose

Record the current knowledge and strategy after the first-candidate mock-only
active test design.

This checkpoint preserves the reasoning we acquired before adding more scope:

- what is now known
- what remains deliberately absent
- how to think about parallel work safely
- which skills/workflows are useful next
- what the next recommended slice should be

This is documentation-only. It adds no implementation, tests, MIDI behavior,
port opening, active execution, CLI execution, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- bd930f6 Add first-candidate mock-only active test design

Current phase:

- Passive/Mock Foundation Phase
- first-candidate mock-only active test design created
- safe parallelization planning now recommended

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Knowledge Preserved

The project is now organized enough to benefit from parallel thinking, but not
from unrestricted parallel implementation.

The safe lesson is:

- maximize clarity before maximizing concurrency
- split work into independent lanes
- keep each lane behind the existing passive/mock boundaries
- use closeout as the synchronization point between lanes
- avoid widening scope while the first candidate is still under review

## 4. Current Technical Boundary

The first mock-only active test candidate is:

- group profile `"2"` / My BD Hard

Current mock mapper support remains:

- group profile `"2"` / My BD Hard
- group profile `"3"` / My BD Classic

Current unsupported/safe profile remains:

- group profile `"4"` / My BD Acoustic

Profile `"4"` remains parked unless separately approved.

## 5. Safe Parallel Workstream Idea

Future work can be split into lanes, as long as each lane remains small and
independent.

Candidate lanes:

- docs and roadmap updates
- mock-only test design
- passive CLI/report visibility
- closeout and safety audits
- future active planning documents

These lanes should not all implement behavior at once. They are a planning
tool for keeping future work organized.

## 6. Skills And Workflow Lessons

Useful workflow skills for future slices:

- writing plans before multi-step implementation
- test-driven development before any mock-only behavior change
- verification before completion before claiming success
- systematic debugging if any closeout step fails
- subagent-driven development only when tasks are independent and explicitly approved

The next slice should likely be a documentation-only safe parallel workstream
plan. It should define lanes, dependencies, stop conditions, and what is not
allowed in each lane.

## 7. What Remains Intentionally Absent

- real MIDI
- mido
- MIDI port opening
- MIDI sending
- active execution
- active CLI command
- CLI wiring to active behavior
- dispatch
- hardware behavior
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- execute-command
- send-command
- hardware-test
- profile `"4"` implementation
- hardware validation

## 8. Safety Invariants

- V1.34 reference remains untouched.
- Passive CLI remains read-only.
- Mock MIDI remains test-only/inert.
- Mock message mapper remains test-only/inert.
- Mock mapper report remains read-only.
- First-candidate design remains documentation-only.
- Hardware remains off.
- No real MIDI libraries are required.

## 9. Next Recommended Task

Create a documentation-only safe parallel workstream plan.

That plan should define:

- lanes
- lane owners/responsibilities
- dependencies
- allowed work
- forbidden work
- synchronization points
- closeout requirements
- when subagents would be useful
- when subagents should not be used

Hardware remains off.

## 10. Decision

Progress and acquired knowledge are saved in this checkpoint.

The next recommended task is a docs-only safe parallel workstream plan.

No implementation in this slice.
