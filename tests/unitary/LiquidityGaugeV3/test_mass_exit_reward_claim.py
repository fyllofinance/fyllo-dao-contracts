import math

import pytest
from brownie import ZERO_ADDRESS

REWARD = 10 ** 10
WEEK = 7 * 86400

WEEK_REWARD = REWARD * WEEK

@pytest.fixture(scope="module", autouse=True)
def initial_setup(
    alice,
    accounts,
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
    coin_deposit.mint(alice, 10 ** 20, {"from": alice})

    for acct in accounts[:10]:
        coin_deposit.transfer(acct, 10 ** 18, {"from": alice})
        coin_deposit.approve(mock_lp_token, 2 ** 256 - 1, {"from": acct})
        mock_lp_token.deposit(10 ** 18, {"from": acct})

    # fund rewards
    coin_reward._mint_for_testing(gauge_v3, WEEK_REWARD + 10 * REWARD) # add 10 seconds reward
    gauge_v3.add_reward_token(coin_reward, REWARD, {"from": alice})

    # sleep half way through the reward period
    chain.sleep(WEEK)


def test_mass_withdraw_claim_rewards(accounts, gauge_v3, coin_reward, mock_lp_token):
    for account in accounts[:10]:
        mock_lp_token.withdraw(mock_lp_token.balanceOf(account), {"from": account})
        assert gauge_v3.claimed_reward(account, coin_reward) == 0
        assert gauge_v3.claimable_reward_write.call(account, coin_reward) > 0

    for account in accounts[:10]:
        gauge_v3.claim_rewards({"from": account})
        assert math.isclose(coin_reward.balanceOf(account), WEEK_REWARD / 10, abs_tol = REWARD)
