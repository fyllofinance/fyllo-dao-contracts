import pytest
from brownie import ZERO_ADDRESS

from tests.conftest import approx

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18

WEEK_REWARD = REWARD * WEEK

@pytest.fixture(scope="module", autouse=True)
def initial_setup(
    alice,
    bob,
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
    coin_deposit.mint(bob, LP_AMOUNT, {"from": alice})
    coin_deposit.approve(mock_lp_token, LP_AMOUNT, {"from": bob})
    mock_lp_token.deposit(LP_AMOUNT, {"from": bob})

    # fund rewards
    coin_reward._mint_for_testing(gauge_v3, WEEK_REWARD + 10 * REWARD) # add 10 seconds reward
    gauge_v3.add_reward_token(coin_reward, REWARD, {"from": alice})


def test_claim_one_lp(bob, chain, gauge_v3, coin_reward, mock_lp_token):
    chain.sleep(WEEK)

    mock_lp_token.withdraw(LP_AMOUNT, {"from": bob})
    gauge_v3.claim_rewards({"from": bob})

    reward = coin_reward.balanceOf(bob)
    assert approx(WEEK_REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s


def test_claim_for_other(bob, charlie, chain, gauge_v3, coin_reward, mock_lp_token):
    chain.sleep(WEEK)

    mock_lp_token.withdraw(LP_AMOUNT, {"from": bob})
    gauge_v3.claim_rewards(bob, {"from": charlie})

    assert coin_reward.balanceOf(charlie) == 0

    reward = coin_reward.balanceOf(bob)
    assert approx(WEEK_REWARD, reward, 1.001 / WEEK)  # ganache-cli jitter of 1 s


def test_claim_for_other_no_reward(bob, charlie, chain, gauge_v3, coin_reward):
    chain.sleep(WEEK)
    gauge_v3.claim_rewards(charlie, {"from": bob})

    assert coin_reward.balanceOf(bob) == 0
    assert coin_reward.balanceOf(charlie) == 0


def test_claim_two_lp(alice, bob, chain, gauge_v3, coin_deposit, mock_lp_token, coin_reward, no_call_coverage):

    # Deposit
    coin_deposit.mint(alice, LP_AMOUNT, {"from": alice})
    coin_deposit.approve(mock_lp_token, LP_AMOUNT, {"from": alice})
    mock_lp_token.deposit(LP_AMOUNT, {"from": alice})

    chain.sleep(WEEK)
    chain.mine()

    # Calculate rewards
    claimable_rewards = [
        gauge_v3.claimable_reward_write.call(acc, coin_reward, {"from": acc})
        for acc in (alice, bob)
    ]

    # Claim rewards
    rewards = []
    for acct in (alice, bob):
        gauge_v3.claim_rewards({"from": acct})
        rewards += [coin_reward.balanceOf(acct)]

    # Calculation == results
    assert tuple(claimable_rewards) == tuple(rewards)

    # Approximately equal apart from what caused by 1 s ganache-cli jitter
    assert approx(rewards[0], rewards[1], 2.002 * WEEK)

