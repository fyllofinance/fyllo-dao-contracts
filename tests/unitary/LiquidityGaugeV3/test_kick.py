import brownie

MAX_UINT256 = 2 ** 256 - 1
WEEK = 7 * 86400


def test_kick(chain, accounts, gauge_v3, voting_escrow, token, coin_deposit, mock_lp_token):
    alice, bob = accounts[:2]
    chain.sleep(2 * WEEK + 5)

    token.mint(alice, 10 ** 20, {"from": alice})
    token.approve(voting_escrow, MAX_UINT256, {"from": alice})
    voting_escrow.create_lock(10 ** 20, chain.time() + 4 * WEEK, {"from": alice})

    coin_deposit.mint(alice, 10 ** 21, {"from": alice})
    coin_deposit.approve(mock_lp_token, MAX_UINT256, {"from": alice})
    mock_lp_token.deposit(10 ** 21, {"from": alice})

    assert gauge_v3.working_balances(alice) == 10 ** 21

    chain.sleep(WEEK)

    with brownie.reverts("dev: kick not allowed"):
        gauge_v3.kick(alice, {"from": bob})

    chain.sleep(4 * WEEK)

    gauge_v3.kick(alice, {"from": bob})
    assert gauge_v3.working_balances(alice) == 4 * 10 ** 20

    with brownie.reverts("dev: kick not needed"):
        gauge_v3.kick(alice, {"from": bob})
