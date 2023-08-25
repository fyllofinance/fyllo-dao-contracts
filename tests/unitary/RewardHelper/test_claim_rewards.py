import brownie
import pytest
import itertools

from brownie import ZERO_ADDRESS

LP_AMOUNT = 1e18
WEEK = 7 * 86400
MONTH = 86400 * 30

@pytest.fixture(scope="module", autouse=True)
def setup(accounts, three_gauges, gauge_controller, chain,
        coin_a, coin_b, coin_c, mock_lp_token_A, mock_lp_token_B, mock_lp_token_C):

    gauge_controller.add_type(b"Liquidity", 5e17, {"from": accounts[0]})
    for i in range(3):
        gauge_controller.add_gauge(
            three_gauges[i], 0, 1e18, {"from": accounts[0]}
        )


    # transfer tokens
    for acct in accounts[1:4]:
        coin_a._mint_for_testing(acct, LP_AMOUNT)
        coin_b._mint_for_testing(acct, LP_AMOUNT)
        coin_c._mint_for_testing(acct, LP_AMOUNT)


    # approve gauges
    for gauge, acct in itertools.product(three_gauges, accounts[1:4]):
        coin_a.approve(mock_lp_token_A, LP_AMOUNT, {"from": acct})
        coin_b.approve(mock_lp_token_B, LP_AMOUNT, {"from": acct})
        coin_c.approve(mock_lp_token_C, LP_AMOUNT, {"from": acct})

    coin_b._mint_for_testing(accounts[1], LP_AMOUNT)
    coin_c._mint_for_testing(accounts[1], LP_AMOUNT)
    coin_b.approve(mock_lp_token_B, LP_AMOUNT, {"from": accounts[1]})
    coin_c.approve(mock_lp_token_C, LP_AMOUNT, {"from": accounts[1]})

def test_claim_not_toggle_approve(minter, three_gauges, mock_lp_token_A, accounts, reward_helper, token, chain):
    mock_lp_token_A.deposit(LP_AMOUNT, {"from": accounts[1]})

    chain.sleep(WEEK)
    chain.mine()

    reward_helper.claim_rewards_for(accounts[1],
        [three_gauges[0], ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS,
        ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS])
    assert token.balanceOf(accounts[1]) == 0

def test_claim_single(minter, three_gauges, mock_lp_token_A, accounts, reward_helper, token, chain):
    mock_lp_token_A.deposit(LP_AMOUNT, {"from": accounts[1]})
    minter.toggle_approve_mint(reward_helper, {"from": accounts[1]})

    chain.sleep(MONTH)
    chain.mine()

    reward_helper.claim_rewards_for(accounts[1],
        [three_gauges[0],
        ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS,
        ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS])

    expected = three_gauges[0].integrate_fraction(accounts[1])
    final_balance = token.balanceOf(accounts[1])

    assert final_balance > 0
    assert final_balance == expected
    assert minter.minted(accounts[1], three_gauges[0]) == expected

def test_claim_multiple_user(accounts, three_gauges, chain,
        mock_lp_token_A, mock_lp_token_B, mock_lp_token_C, reward_helper, token, minter):
    mock_lp_token_A.deposit(LP_AMOUNT, {"from": accounts[1]})
    minter.toggle_approve_mint(reward_helper, {"from": accounts[1]})

    chain.sleep(WEEK)
    chain.mine()

    mock_lp_token_B.deposit(LP_AMOUNT, {"from": accounts[2]})
    minter.toggle_approve_mint(reward_helper, {"from": accounts[2]})

    chain.sleep(WEEK)
    chain.mine()

    mock_lp_token_C.deposit(LP_AMOUNT, {"from": accounts[3]})
    minter.toggle_approve_mint(reward_helper, {"from": accounts[3]})

    chain.sleep(MONTH)
    chain.mine()

    reward_helper.claim_rewards_for(accounts[1],
        [three_gauges[0],
        three_gauges[1], three_gauges[2], ZERO_ADDRESS, ZERO_ADDRESS,
        ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS])
    expected1 = three_gauges[0].integrate_fraction(accounts[1])
    final_balance1 = token.balanceOf(accounts[1])

    assert final_balance1 > 0
    assert final_balance1 == expected1
    assert minter.minted(accounts[1], three_gauges[0]) == expected1

    reward_helper.claim_rewards_for(accounts[2],
        [three_gauges[0],
        three_gauges[1], three_gauges[2], ZERO_ADDRESS, ZERO_ADDRESS,
        ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS])
    expected2 = three_gauges[1].integrate_fraction(accounts[2])
    final_balance2 = token.balanceOf(accounts[2])

    assert final_balance2 > 0
    assert final_balance2 == expected2
    assert minter.minted(accounts[2], three_gauges[1]) == expected2

    reward_helper.claim_rewards_for(accounts[3],
        [three_gauges[0],
        three_gauges[1], three_gauges[2], ZERO_ADDRESS, ZERO_ADDRESS,
        ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS])
    expected3 = three_gauges[2].integrate_fraction(accounts[3])
    final_balance3 = token.balanceOf(accounts[3])

    assert final_balance3 > 0
    assert final_balance3 == expected3
    assert minter.minted(accounts[3], three_gauges[2]) == expected3

def test_claim_multiple_gauge(accounts, three_gauges, chain,
        mock_lp_token_A, mock_lp_token_B, mock_lp_token_C, reward_helper, token, minter):

    minter.toggle_approve_mint(reward_helper, {"from": accounts[1]})

    mock_lp_token_A.deposit(LP_AMOUNT, {"from": accounts[1]})
    mock_lp_token_B.deposit(LP_AMOUNT, {"from": accounts[1]})
    mock_lp_token_C.deposit(LP_AMOUNT, {"from": accounts[1]})

    chain.sleep(MONTH)
    chain.mine()

    reward_helper.claim_rewards_for(accounts[1],
        [three_gauges[0],
        three_gauges[1], three_gauges[2], ZERO_ADDRESS, ZERO_ADDRESS,
        ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS])

    expected = 0
    minted = 0
    for i in range(3):
        expected += three_gauges[i].integrate_fraction(accounts[1])
        minted += minter.minted(accounts[1], three_gauges[i])

    final_balance = token.balanceOf(accounts[1])

    assert final_balance > 0
    assert final_balance == expected
    assert minted == final_balance

def test_claim_multiple_rewards(accounts, three_gauges, chain, mock_lp_token_A, reward_helper, token, minter, coin_reward):
    minter.toggle_approve_mint(reward_helper, {"from": accounts[1]})

    three_gauges[0].add_reward_token(coin_reward, 10 ** 18, {"from": accounts[0]})
    coin_reward._mint_for_testing(three_gauges[0], 10 ** 18 * MONTH)

    mock_lp_token_A.deposit(LP_AMOUNT, {"from": accounts[1]})

    chain.sleep(2 * WEEK)
    chain.mine()

    reward_helper.claim_rewards_for(accounts[1],
        [three_gauges[0],
        three_gauges[1], three_gauges[2], ZERO_ADDRESS, ZERO_ADDRESS,
        ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS])

    expected = three_gauges[0].integrate_fraction(accounts[1])
    token_balance = token.balanceOf(accounts[1])

    assert token_balance > 0
    assert token_balance == expected
    assert minter.minted(accounts[1], three_gauges[0]) == expected

    claimed = three_gauges[0].claimed_reward(accounts[1], coin_reward)
    reward_balance = coin_reward.balanceOf(accounts[1])
    assert claimed > 0
    assert claimed == reward_balance


