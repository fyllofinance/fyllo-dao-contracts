import brownie

import pytest
from brownie import ZERO_ADDRESS

LP_AMOUNT = 10 ** 18
REWARD = 10 ** 18

@pytest.fixture(scope="module", autouse=True)
def initial_setup(coin_deposit, mock_lp_token, alice):
    coin_deposit.mint(alice, LP_AMOUNT, {"from": alice})
    coin_deposit.approve(mock_lp_token, LP_AMOUNT, {"from": alice})


def test_add_reward_token_no_rate(alice, gauge_v3, coin_reward):
    gauge_v3.add_reward_token(coin_reward, 0, {"from": alice})

    assert gauge_v3.reward_token_length() == 1
    assert gauge_v3.reward_tokens(0) == coin_reward
    assert gauge_v3.reward_tokens(1) == ZERO_ADDRESS
    assert gauge_v3.reward_rate(coin_reward) == 0


def test_add_reward_token(alice, gauge_v3, coin_reward):
    gauge_v3.add_reward_token(coin_reward, REWARD, {"from": alice})

    assert gauge_v3.reward_token_length() == 1
    assert gauge_v3.reward_tokens(0) == coin_reward
    assert gauge_v3.reward_tokens(1) == ZERO_ADDRESS
    assert gauge_v3.reward_rate(coin_reward) == REWARD


def test_add_reward_token_deposit(alice, gauge_v3, mock_lp_token, coin_reward):
    mock_lp_token.deposit(LP_AMOUNT, {"from": alice})
    gauge_v3.add_reward_token(coin_reward, REWARD, {"from": alice})

    assert gauge_v3.balanceOf(alice) == LP_AMOUNT
    assert gauge_v3.reward_token_length() == 1
    assert gauge_v3.reward_tokens(0) == coin_reward
    assert gauge_v3.reward_tokens(1) == ZERO_ADDRESS
    assert gauge_v3.reward_rate(coin_reward) == REWARD

def test_add_multiple_reward_token(alice, gauge_v3, coin_reward, coin_a, coin_b):
    gauge_v3.add_reward_token(coin_reward, REWARD, {"from": alice})
    gauge_v3.add_reward_token(coin_a, REWARD, {"from": alice})
    gauge_v3.add_reward_token(coin_b, REWARD, {"from": alice})

    reward_tokens = [coin_reward, coin_a, coin_b] + [ZERO_ADDRESS] * 5

    assert gauge_v3.reward_token_length() == 3
    assert reward_tokens == [gauge_v3.reward_tokens(i) for i in range(8)]
    for i in range(8):
        if reward_tokens[i] != ZERO_ADDRESS:
            assert gauge_v3.reward_rate(reward_tokens[i]) == REWARD

def test_add_exist_reward_token(alice, gauge_v3, coin_reward):
    gauge_v3.add_reward_token(coin_reward, REWARD, {"from": alice})

    with brownie.reverts("dev: the reward token is added"):
        gauge_v3.add_reward_token(coin_reward, REWARD, {"from": alice})

def test_add_admin_only(bob, gauge_v3, coin_reward):
    with brownie.reverts("dev: admin only"):
        gauge_v3.add_reward_token(coin_reward, REWARD, {"from": bob})
