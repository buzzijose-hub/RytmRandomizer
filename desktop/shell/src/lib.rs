//! RytmRandomizer Tauri shell library.
//!
//! Exposed as a library so the sidecar-supervision and update modules can be
//! unit-tested without spinning up the full Tauri runtime.
//!
//! The update subsystem is split three ways on purpose (R3):
//!
//! * [`update_policy`] — the pure `(state, event, config) -> (state, effects)`
//!   core. No network, no filesystem, no Tauri, no clock reads.
//! * [`update_journal`] — the JSONL writer for the closed event vocabulary
//!   (contract I8), size-capped with two-generation rotation.
//! * [`updater`] — the thin driver that performs the effects the policy
//!   describes and feeds their outcomes back in as events.

pub mod sidecar;
pub mod update_commands;
pub mod update_journal;
pub mod update_policy;
pub mod update_transport;
pub mod updater;
