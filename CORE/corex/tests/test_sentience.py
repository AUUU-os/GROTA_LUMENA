import pytest
import asyncio
from corex.sentience import sentience

@pytest.mark.asyncio
async def test_sentience_initialization():
    assert sentience.alive is True
    assert sentience.mode == "SENTIENT_MODE"
    assert "valence" in sentience.emotion

@pytest.mark.asyncio
async def test_inner_dialog():
    response = await sentience.think("Test input for resonance")
    assert "Inner Consensus" in response
    assert "[" in response # Checks for emotion tags
