from brownie import ZERO_ADDRESS

REWARD = 10 ** 20
WEEK = 7 * 86400
LP_AMOUNT = 10 ** 18


def test_claim_no_deposit(alice, bob, chain, gauge_v3, coin_deposit, mock_lp_token, coin_reward):
    # Fund
    coin_deposit.mint(alice, LP_AMOUNT, {"from": alice})
    coin_deposit.approve(mock_lp_token, LP_AMOUNT, {"from": alice})
    mock_lp_token.deposit(LP_AMOUNT, {"from": alice})

    coin_reward._mint_for_testing(gauge_v3, REWARD * WEEK)
    gauge_v3.add_reward_token(coin_reward, REWARD, {"from": alice})

    chain.sleep(WEEK)

    gauge_v3.claim_rewards({"from": bob})

    assert coin_reward.balanceOf(bob) == 0


def test_claim_no_rewards(alice, bob, chain, gauge_v3, coin_deposit, mock_lp_token, coin_reward):
    # Deposit
    coin_deposit.mint(bob, LP_AMOUNT, {"from": alice})
    coin_deposit.approve(mock_lp_token, LP_AMOUNT, {"from": bob})
    mock_lp_token.deposit(LP_AMOUNT, {"from": bob})

    chain.sleep(WEEK)

    mock_lp_token.withdraw(LP_AMOUNT, {"from": bob})
    gauge_v3.claim_rewards({"from": bob})

    assert coin_reward.balanceOf(bob) == 0
