import math

import pytest
from brownie import ZERO_ADDRESS

REWARD = 10 ** 20
WEEK = 7 * 86400

WEEK_REWARD = REWARD * WEEK

@pytest.fixture(scope="module", autouse=True)
def initial_setup(
    alice,
    chain,
    coin_reward,
    coin_deposit,
    mock_lp_token,
    gauge_v3,
    gauge_controller,
    minter,
):
    # gauge setup
    gauge_controller.add_type(b"Liquidity", 10 ** 10, {"from": alice})
    gauge_controller.add_gauge(gauge_v3, 0, 0, {"from": alice})

    # deposit into gauge
    coin_deposit.mint(alice, 10 ** 22, {"from": alice})
    coin_deposit.approve(mock_lp_token, 2 ** 256 - 1, {"from": alice})
    mock_lp_token.deposit(10 ** 18, {"from": alice})

    coin_reward._mint_for_testing(gauge_v3, REWARD * WEEK * 3.5)
    gauge_v3.add_reward_token(coin_reward, REWARD, {"from": alice})

    # sleep half way through the reward period
    chain.sleep(int(86400 * 3.5))


def test_transfer_does_not_trigger_claim_for_sender(alice, bob, chain, gauge_v3, coin_reward, mock_lp_token):
    amount = mock_lp_token.balanceOf(alice)

    mock_lp_token.transfer(bob, amount, {"from": alice})

    reward = coin_reward.balanceOf(alice)
    assert reward == 0


def test_transfer_does_not_trigger_claim_for_receiver(alice, bob, chain, gauge_v3, coin_reward, mock_lp_token):
    amount = mock_lp_token.balanceOf(alice) // 2

    mock_lp_token.transfer(bob, amount, {"from": alice})
    chain.sleep(WEEK)
    mock_lp_token.transfer(alice, amount, {"from": bob})

    for acct in (alice, bob):
        assert coin_reward.balanceOf(acct) == 0


def test_claim_rewards_stil_accurate(alice, bob, chain, gauge_v3, coin_reward, mock_lp_token):
    amount = mock_lp_token.balanceOf(alice)

    mock_lp_token.transfer(bob, amount, {"from": alice})

    # sleep half way through the reward period
    chain.sleep(int(86400 * 3.5))

    for acct in (alice, bob):
        gauge_v3.claim_rewards({"from": acct})

        assert math.isclose(coin_reward.balanceOf(acct), WEEK_REWARD // 2, rel_tol=0.01)
