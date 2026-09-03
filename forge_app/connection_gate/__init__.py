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
