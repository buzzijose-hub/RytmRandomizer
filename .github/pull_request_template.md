# Pull Request Checklist

## Summary

- What changed:
- Why it changed:

## Verification

- [ ] Ran `python -m pytest`
- [ ] Closeout ran: `powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1`
- [ ] Checked project-status output when relevant

## Safety

- [ ] V1.34 impact is described, or no V1.34 behavior changed
- [ ] No unintended MIDI imports
- [ ] No unintended MIDI port opening
- [ ] No unintended MIDI sending
- [ ] No unintended active behavior
- [ ] No unintended hardware requirement

## Docs

- [ ] README / CONTRIBUTING / Docs updated if structure changed
- [ ] Changelog updated if user-visible behavior changed
