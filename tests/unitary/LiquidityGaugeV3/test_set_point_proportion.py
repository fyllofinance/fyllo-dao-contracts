import brownie
import brownie

import pytest
from brownie import ZERO_ADDRESS

LP_AMOUNT = 10 ** 18
PROPORTION = 10 ** 16

@pytest.fixture(scope="module", autouse=True)
def initial_setup(alice, gauge_v3, coin_deposit, mock_lp_token):
    coin_deposit.mint(alice, LP_AMOUNT, {"from": alice})
    coin_deposit.approve(mock_lp_token, LP_AMOUNT, {"from": alice})

def test_set_proportion(alice, gauge_v3):
    gauge_v3.set_point_proportion(PROPORTION, {"from": alice})

    assert gauge_v3.point_proportion() == PROPORTION


def test_set_proportion_deposit(alice, gauge_v3, mock_lp_token):
    mock_lp_token.deposit(LP_AMOUNT, {"from": alice})
    gauge_v3.set_point_proportion(PROPORTION, {"from": alice})

    assert gauge_v3.balanceOf(alice) == LP_AMOUNT
    assert gauge_v3.point_proportion() == PROPORTION


def test_set_admin_only(bob, gauge_v3):
    with brownie.reverts("dev: admin only"):
        gauge_v3.set_point_proportion(PROPORTION, {"from": bob})
