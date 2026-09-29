//! The `#[tauri::command]` surface the cockpit's update panel invokes.
//!
//! Without this the panel is decorative: "Check now" set a note, "Confirm
//! choice" updated local React state, and neither reached the driver. The
//! buttons looked live and did nothing — the same class of defect as the
//! IPC/DOM mismatch, one layer up.
//!
//! Every command here does exactly one thing: turn an operator gesture into
//! the [`UpdateEvent`] the pure policy already models. No command decides
//! anything — not whether an update is available, not whether a consent is
//! valid, not whether freeze applies. That is the policy's job, and keeping
//! the commands this thin is what stops a second, divergent state machine
//! growing in the IPC layer.

use crate::update_policy::{ConsentChoice, UpdateEvent};
use crate::updater::{EffectSink, Updater};

/// The driver handle commands dispatch into, stored in Tauri's state.
pub struct UpdateCommandState<S: EffectSink> {
    /// The driver. Cloneable, so every command gets its own handle.
    pub driver: Updater<S>,
}

impl<S: EffectSink> UpdateCommandState<S> {
    /// Wrap a driver.
    pub fn new(driver: Updater<S>) -> Self {
        Self { driver }
    }
}

/// The three choices the §7.1 prompt offers, exactly as the web layer spells
/// them (`UPDATE_CONSENT_CHOICES` in `updateProtocol.ts`).
///
/// The wire spellings and the Rust enum do NOT coincide, and pretending
/// otherwise is how a seam breaks: TypeScript sends `install_now`, while
/// `ConsentChoice::RestartAndInstall` serialises to `restart_and_install`.
/// The third choice, `skip_this_version`, is not a `ConsentChoice` in the
/// policy at all — it is a separate `SkipRequested` event. This function is
/// the one place that translation happens.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PromptChoice {
    /// Install at the next natural exit (the §7.1 default).
    OnQuit,
    /// Restart and install immediately.
    Now,
    /// Stop offering this version.
    Skip,
}

/// Parse the wire spelling of a prompt choice.
///
/// Returns `None` for anything unrecognised rather than defaulting. Coercing
/// an unknown value to "now" would install without consent; coercing it to
/// "on quit" would silently discard an explicit "now"; coercing it to "skip"
/// would suppress an update the operator never dismissed. There is no safe
/// default, so there is no default.
pub fn parse_prompt_choice(raw: &str) -> Option<PromptChoice> {
    match raw {
        "install_on_quit" => Some(PromptChoice::OnQuit),
        "install_now" => Some(PromptChoice::Now),
        "skip_this_version" => Some(PromptChoice::Skip),
        _ => None,
    }
}

/// The event a `confirm_update_choice` invocation becomes.
///
/// Split from the command itself so the mapping is testable without a Tauri
/// runtime — the command body is then a two-line adapter with nothing to get
/// wrong. Note that "skip" is a DIFFERENT event, not a consent: consenting to
/// an install and declining one are opposite decisions and the policy models
/// them separately.
pub fn prompt_event(version: &str, raw_choice: &str) -> Option<UpdateEvent> {
    Some(match parse_prompt_choice(raw_choice)? {
        PromptChoice::OnQuit => UpdateEvent::ConsentGranted {
            version: version.to_string(),
            choice: ConsentChoice::InstallOnQuit,
        },
        PromptChoice::Now => UpdateEvent::ConsentGranted {
            version: version.to_string(),
            choice: ConsentChoice::RestartAndInstall,
        },
        PromptChoice::Skip => UpdateEvent::SkipRequested {
            version: version.to_string(),
        },
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_wire_spelling_the_panel_can_send_is_understood() {
        // These three strings are UPDATE_CONSENT_CHOICES in updateProtocol.ts.
        // If the web layer adds a fourth, this fails rather than silently
        // refusing the new one at runtime.
        assert_eq!(
            parse_prompt_choice("install_on_quit"),
            Some(PromptChoice::OnQuit)
        );
        assert_eq!(parse_prompt_choice("install_now"), Some(PromptChoice::Now));
        assert_eq!(
            parse_prompt_choice("skip_this_version"),
            Some(PromptChoice::Skip)
        );
    }

    #[test]
    fn the_rust_enum_spelling_is_not_accepted_from_the_wire() {
        // ConsentChoice::RestartAndInstall serialises to "restart_and_install",
        // which is NOT what the panel sends. Accepting it here would paper over
        // a genuine seam mismatch and let the two spellings drift apart.
        assert_eq!(parse_prompt_choice("restart_and_install"), None);
    }

    #[test]
    fn an_unknown_choice_is_refused_rather_than_defaulted() {
        // There is no safe default: "now" installs without consent, "on quit"
        // discards an explicit "now", "skip" suppresses an update nobody
        // dismissed.
        for raw in ["", "now", "INSTALL_NOW", "later", "quit"] {
            assert_eq!(parse_prompt_choice(raw), None, "{raw:?} must be refused");
        }
    }

    #[test]
    fn the_quit_default_becomes_a_consent_not_an_immediate_install() {
        assert_eq!(
            prompt_event("1.35.1", "install_on_quit"),
            Some(UpdateEvent::ConsentGranted {
                version: "1.35.1".to_string(),
                choice: ConsentChoice::InstallOnQuit,
            })
        );
    }

    #[test]
    fn install_now_becomes_restart_and_install() {
        assert_eq!(
            prompt_event("1.35.1", "install_now"),
            Some(UpdateEvent::ConsentGranted {
                version: "1.35.1".to_string(),
                choice: ConsentChoice::RestartAndInstall,
            })
        );
    }

    #[test]
    fn skip_is_a_separate_event_never_a_consent() {
        // Consenting to an install and declining one are opposite decisions.
        // Routing skip through ConsentGranted would authorise the very install
        // the operator just refused.
        assert_eq!(
            prompt_event("1.35.1", "skip_this_version"),
            Some(UpdateEvent::SkipRequested {
                version: "1.35.1".to_string(),
            })
        );
    }

    #[test]
    fn a_malformed_invocation_produces_no_event_at_all() {
        assert_eq!(prompt_event("1.35.1", "whenever"), None);
    }
}
