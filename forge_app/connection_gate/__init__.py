"""Singularity Works external authority / Connection Gate substrate."""

from .authority import (
    AuthorityDecision,
    ConsequenceClass,
    ConnectionDecisionReceipt,
    ConnectorPolicy,
    CredentialCeiling,
    CurrentnessState,
    GrantState,
    IntentSource,
    OperationConfirmation,
    OperationRequest,
    ProviderIdentity,
    SessionArming,
    UserGrant,
    VerificationState,
    evaluate_connection_authority,
)

__all__ = [
    "AuthorityDecision",
    "ConsequenceClass",
    "ConnectionDecisionReceipt",
    "ConnectorPolicy",
    "CredentialCeiling",
    "CurrentnessState",
    "GrantState",
    "IntentSource",
    "OperationConfirmation",
    "OperationRequest",
    "ProviderIdentity",
    "SessionArming",
    "UserGrant",
    "VerificationState",
    "evaluate_connection_authority",
]

from .authority_state import (
    AuthorityStateError,
    ConnectionAuthorityStateStore,
    OperationStage,
    PersistedDecision,
    PreparedOperation,
)

__all__ += [
    "AuthorityStateError",
    "ConnectionAuthorityStateStore",
    "OperationStage",
    "PersistedDecision",
    "PreparedOperation",
]

from .operation_lifecycle import (
    ExternalOperation,
    ExternalOperationLifecycleStore,
    LifecycleState,
    LifecycleView,
    OperationLifecycleError,
    RemoteOutcome,
)

__all__ += [
    "ExternalOperation",
    "ExternalOperationLifecycleStore",
    "LifecycleState",
    "LifecycleView",
    "OperationLifecycleError",
    "RemoteOutcome",
]
