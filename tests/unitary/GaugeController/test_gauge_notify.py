import brownie

import pytest

LP_AMOUNT = 10 ** 18

@pytest.fixture(scope="module", autouse=True)
def initial_setup(coin_deposit, mock_lp_token_v2, accounts):
    coin_deposit.mint(accounts[0], LP_AMOUNT, {"from": accounts[0]})
    coin_deposit.approve(mock_lp_token_v2, LP_AMOUNT, {"from": accounts[0]})

def test_gauge_notify_not_added(gauge_controller, accounts, mock_lp_token_v2):
    mock_lp_token_v2.deposit(LP_AMOUNT, {"from": accounts[0]})


def test_gauge_notify(gauge_controller, accounts, gauge_for_mock_v2, mock_lp_token_v2):
    gauge_controller.add_gauge(gauge_for_mock_v2, 0, {"from": accounts[0]})
    assert gauge_controller.gauges_lptoken(mock_lp_token_v2) == gauge_for_mock_v2.address

    mock_lp_token_v2.deposit(LP_AMOUNT, {"from": accounts[0]})
    assert gauge_for_mock_v2.balanceOf(accounts[0]) == LP_AMOUNT
