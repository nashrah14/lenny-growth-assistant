"""
Unit Tests for Intent Router
"""
import pytest
from backend.app.agents.router import IntentRouter, IntentType

def test_intent_router_normal_qa():
    assert IntentRouter.classify("How does Superhuman measure product market fit?") == IntentType.NORMAL_QA
    assert IntentRouter.classify("What did Brian Chesky say about founder mode?") == IntentType.NORMAL_QA
    assert IntentRouter.classify("Explain retention curves for B2B SaaS") == IntentType.NORMAL_QA

def test_intent_router_ship30():
    assert IntentRouter.classify("Write a Ship 30 for 30 essay on Elena Verna's PLG loops") == IntentType.SHIP30
    assert IntentRouter.classify("Generate an atomic essay about onboarding frameworks") == IntentType.SHIP30
    assert IntentRouter.classify("Write an article summarizing Lenny's interview with Shreyas Doshi") == IntentType.SHIP30

def test_intent_router_artifact():
    assert IntentRouter.classify("Create an interactive CAC and LTV calculator component") == IntentType.ARTIFACT
    assert IntentRouter.classify("Build a product launch checklist artifact") == IntentType.ARTIFACT
    assert IntentRouter.classify("Generate an HTML retention heatmap dashboard") == IntentType.ARTIFACT

def test_intent_router_explicit_override():
    assert IntentRouter.classify("Random text", explicit_intent="SHIP30") == IntentType.SHIP30
    assert IntentRouter.classify("Random text", explicit_intent="ARTIFACT") == IntentType.ARTIFACT
