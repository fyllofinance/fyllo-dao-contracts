import math

import brownie
import pytest
from brownie import ZERO_ADDRESS, compile_source

from tests.conftest import approx

REWARD_RATE = 10 ** 18
WEEK = 7 * 86400
REWARD = REWARD_RATE * WEEK
LP_AMOUNT = 10 ** 18


@pytest.fixture(scope="module", autouse=True)
def initial_setup(
    alice, bob, chain, gauge_v3, coin_deposit, coin_a, coin_b, mock_lp_token
):
    coin_a._mint_for_testing(gauge_v3, REWARD * 2)
    coin_b._mint_for_testing(gauge_v3, REWARD * 2)
    gauge_v3.add_reward_token(coin_a, REWARD_RATE, {"from": alice})
    gauge_v3.add_reward_token(coin_b, REWARD_RATE, {"from": alice})

    # Deposit to gauge
    coin_deposit.mint(bob, LP_AMOUNT, {"from": alice})
    coin_deposit.approve(mock_lp_token, LP_AMOUNT, {"from": bob})
    mock_lp_token.deposit(LP_AMOUNT, {"from": bob})


def test_claim_one_lp(bob, chain, gauge_v3, coin_a, coin_b, mock_lp_token):
    chain.sleep(WEEK)

    mock_lp_token.withdraw(LP_AMOUNT, {"from": bob})
    gauge_v3.claim_rewards({"from": bob})

    for coin in (coin_a, coin_b):
        reward = coin.balanceOf(bob)
        assert approx(REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s


def test_claim_updates_claimed_reward(bob, chain, gauge_v3, coin_a, coin_b, mock_lp_token):
    chain.sleep(WEEK)

    mock_lp_token.withdraw(LP_AMOUNT, {"from": bob})
    gauge_v3.claim_rewards({"from": bob})

    for coin in (coin_a, coin_b):
        reward = coin.balanceOf(bob)
        assert approx(REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s
        assert gauge_v3.claimed_reward(bob, coin) == reward


def test_claim_for_other(bob, charlie, chain, gauge_v3, coin_a, coin_b, mock_lp_token):
    chain.sleep(WEEK)

    mock_lp_token.withdraw(LP_AMOUNT, {"from": bob})
    gauge_v3.claim_rewards(bob, {"from": charlie})

    assert coin_a.balanceOf(charlie) == 0

    for coin in (coin_a, coin_b):
        reward = coin.balanceOf(bob)
        assert approx(REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s


def test_claim_for_other_no_reward(bob, charlie, chain, gauge_v3, coin_a, coin_b):
    chain.sleep(WEEK)
    gauge_v3.claim_rewards(charlie, {"from": bob})

    assert coin_a.balanceOf(bob) == 0
    assert coin_a.balanceOf(charlie) == 0

    assert coin_b.balanceOf(bob) == 0
    assert coin_b.balanceOf(charlie) == 0


def test_claim_two_lp(
    alice, bob, chain, gauge_v3, coin_deposit, mock_lp_token, coin_a, coin_b, no_call_coverage
):
    # Deposit
    coin_deposit.mint(alice, LP_AMOUNT, {"from": alice})
    coin_deposit.approve(mock_lp_token, LP_AMOUNT, {"from": alice})
    mock_lp_token.deposit(LP_AMOUNT, {"from": alice})

    chain.sleep(WEEK)
    chain.mine()

    for acct in (alice, bob):
        gauge_v3.claim_rewards({"from": acct})

    for coin in (coin_a, coin_b):
        # Calculate rewards
        assert coin.balanceOf(bob) >= coin.balanceOf(alice) > 0
        assert coin.balanceOf(gauge_v3) <= REWARD


def test_claim_set_alt_receiver(bob, charlie, chain, gauge_v3, coin_a, coin_b):
    chain.sleep(WEEK)

    gauge_v3.claim_rewards(bob, charlie, {"from": bob})

    assert coin_a.balanceOf(bob) == 0
    assert coin_b.balanceOf(bob) == 0

    for coin in (coin_a, coin_b):
        reward = coin.balanceOf(charlie)
        assert approx(REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s


def test_claim_for_other_changing_receiver_reverts(bob, charlie, chain, gauge_v3, mock_lp_token):
    chain.sleep(WEEK)

    mock_lp_token.withdraw(LP_AMOUNT, {"from": bob})
    with brownie.reverts("dev: cannot redirect when claiming for another user"):
        gauge_v3.claim_rewards(bob, charlie, {"from": charlie})
