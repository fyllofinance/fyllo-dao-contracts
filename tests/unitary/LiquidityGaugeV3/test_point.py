import math

import brownie
import pytest
from brownie import ZERO_ADDRESS

from tests.conftest import approx

WEEK = 7 * 86400
LP_AMOUNT = 10 ** 20

@pytest.fixture(scope="module", autouse=True)
def initial_setup(alice, bob, chain, gauge_v3_point, coin_deposit, mock_lp_token):
    coin_deposit.mint(alice, LP_AMOUNT, {"from": alice})
    coin_deposit.mint(bob, LP_AMOUNT, {"from": alice})
    coin_deposit.approve(mock_lp_token, LP_AMOUNT, {"from": alice})
    coin_deposit.approve(mock_lp_token, LP_AMOUNT, {"from": bob})

    mock_lp_token.deposit(LP_AMOUNT, {"from": alice})


def test_get_point(alice, chain, gauge_v3_point, mock_lp_token):
    chain.sleep(WEEK)
    chain.mine()

    balance = gauge_v3_point.balance_of_write.call(alice, {"from": alice})

    gauge_v3_point.user_checkpoint(alice, {"from": alice})
    expected = gauge_v3_point.point_integrate_fraction(alice)

    assert expected > 0
    assert balance == expected + mock_lp_token.balanceOf(alice)
    assert gauge_v3_point.totalSupply() == balance


def test_point_amount_not_cross(alice, chain, gauge_v3_point, mock_lp_token):
    t0 = chain.time()
    dt = (t0 + WEEK) // WEEK * WEEK - t0
    chain.sleep(dt)
    chain.mine()

    gauge_v3_point.user_checkpoint(alice, {"from": alice})
    expected = gauge_v3_point.point_integrate_fraction(alice)

    cal = 10000 * dt # point rate is 10000 * 10 ** 18

    assert expected > 0
    assert math.isclose(cal, expected, rel_tol=0.0001)

def test_point_amount_cross(alice, chain, gauge_v3_point, mock_lp_token):
    t0 = chain.time()
    next_epoch = (t0 + WEEK) // WEEK * WEEK
    dt1 = next_epoch - t0

    chain.sleep(WEEK)
    chain.mine()

    dt2 = chain.time() - next_epoch

    gauge_v3_point.user_checkpoint(alice, {"from": alice})
    expected = gauge_v3_point.point_integrate_fraction(alice)

    cal = 10000 * dt1 +  LP_AMOUNT * 10 ** 17 // WEEK / 10 ** 18 * dt2

    assert expected > 0
    assert approx(expected, int(cal), 1e-14)

def test_withdraw_point_decrease(alice, chain, gauge_v3_point, mock_lp_token):
    chain.sleep(WEEK)
    chain.mine()

    gauge_v3_point.user_checkpoint(alice, {"from": alice})
    point1 = gauge_v3_point.point_integrate_fraction(alice)
    balance1 = gauge_v3_point.balanceOf(alice)

    mock_lp_token.withdraw(LP_AMOUNT // 2, {"from": alice})
    point2 = gauge_v3_point.point_integrate_fraction(alice)
    balance2 = gauge_v3_point.balanceOf(alice)

    assert point1 > 0 and point2 > 0
    assert point2 == point1 // 2
    assert balance2 == balance1 // 2
    assert gauge_v3_point.totalSupply() - gauge_v3_point.lpTotalSupply() == point2

def test_transfer_point_decrease(alice, bob, chain, gauge_v3_point, mock_lp_token):
    chain.sleep(WEEK)
    chain.mine()

    gauge_v3_point.user_checkpoint(alice, {"from": alice})
    point1 = gauge_v3_point.point_integrate_fraction(alice)

    mock_lp_token.transfer(bob, LP_AMOUNT // 2, {"from": alice})
    point2 = gauge_v3_point.point_integrate_fraction(alice)

    pointBob = gauge_v3_point.point_integrate_fraction(bob)

    assert pointBob == 0
    assert point1 > 0 and point2 > 0
    assert point2 == point1 // 2

def test_point_multiple_user(alice, bob, chain, gauge_v3_point, mock_lp_token):
    chain.sleep(WEEK)
    chain.mine()

    gauge_v3_point.user_checkpoint(alice, {"from": alice})
    point_alice_1 = gauge_v3_point.point_integrate_fraction(alice)

    mock_lp_token.deposit(LP_AMOUNT, {"from": bob})
    point_bob_1 = gauge_v3_point.point_integrate_fraction(bob)

    chain.sleep(WEEK)
    chain.mine()

    gauge_v3_point.user_checkpoint(alice, {"from": alice})
    gauge_v3_point.user_checkpoint(bob, {"from": bob})
    point_alice_2 = gauge_v3_point.point_integrate_fraction(alice)
    point_bob_2 = gauge_v3_point.point_integrate_fraction(bob)

    assert point_alice_1 > 0 and point_bob_1 == 0
    assert point_bob_2 > 0
    assert point_alice_2 > point_bob_2
    assert gauge_v3_point.totalSupply() - gauge_v3_point.lpTotalSupply() == point_alice_2 + point_bob_2
