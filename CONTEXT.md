# Organization foundation

The GitHub-native administrative boundary of Samwise-OS.

## Language

**Baseline**: The declared organization controls and verified operating behavior.
_Avoid_: Platform, runtime

**Authority**: The one version-controlled source responsible for a managed setting.
_Avoid_: Competing source of truth

**Canary**: A bounded repository used to prove provisioning, enforcement and recovery.
_Avoid_: Production project

**Reconciliation**: Convergence of authenticated GitHub state to declared managed values.
_Avoid_: Blind replay

**Acceptance**: Evidence that the intended actor experiences the declared behavior.
_Avoid_: Registration, configuration presence
