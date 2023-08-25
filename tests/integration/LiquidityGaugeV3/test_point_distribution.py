import brownie
from brownie import ZERO_ADDRESS, chain
from brownie.test import strategy

MAX_UINT256 = 2 ** 256 - 1
WEEK = 7 * 86400

LP_AMOUNT = 10 ** 21

def test_point_distribution(accounts, chain, gauge_v3_point, coin_deposit, mock_lp_token):
    alice, bob, charlie = accounts[:3]

    # Let Alice, Bob, charlie have about the same token amount
    for acct in accounts[:3]:
        coin_deposit.mint(acct, LP_AMOUNT, {"from": accounts[0]})
        coin_deposit.approve(mock_lp_token, MAX_UINT256, {"from": acct})

    #alice deposit, alice_point_fraction is zero, the point rate is 10000 * 10 ** 18
    mock_lp_token.deposit(LP_AMOUNT, {"from": alice})

    #sleep over the first epoch
    t0 = chain.time()
    chain.sleep((t0 + WEEK) // WEEK * WEEK - t0)
    chain.mine()

    gauge_v3_point.user_checkpoint(alice, {"from": alice})
    old_alice_point_fraction = gauge_v3_point.point_integrate_fraction(alice)

    # bob deposit, this epoch the point rate is LP_AMOUNT * 10 ** 17 / WEEK
    mock_lp_token.deposit(LP_AMOUNT, {"from": bob})
    old_bob_point_fraction = gauge_v3_point.point_integrate_fraction(bob)
    assert old_bob_point_fraction == 0

    # sleep over an epoch
    chain.sleep(WEEK)
    chain.mine()

    gauge_v3_point.user_checkpoint(alice, {"from": alice})
    gauge_v3_point.user_checkpoint(bob, {"from": bob})
    alice_point_fraction = gauge_v3_point.point_integrate_fraction(alice)
    bob_point_fraction = gauge_v3_point.point_integrate_fraction(bob)

    d_alice = alice_point_fraction - old_alice_point_fraction

    # Alice earned the same as Bob now
    assert d_alice == bob_point_fraction

    # charlie deposit, this epoch the point rate is 2 * LP_AMOUNT * 10 ** 17 / WEEK
    mock_lp_token.deposit(LP_AMOUNT, {"from": charlie})
    old_charlie_point_fraction = gauge_v3_point.point_integrate_fraction(charlie)
    assert old_charlie_point_fraction == 0

    # sleep over an epoch
    chain.sleep(WEEK)
    chain.mine()

    gauge_v3_point.user_checkpoint(alice, {"from": alice})
    gauge_v3_point.user_checkpoint(bob, {"from": bob})
    gauge_v3_point.user_checkpoint(charlie, {"from": charlie})
    new_alice_point_fraction = gauge_v3_point.point_integrate_fraction(alice)
    new_bob_point_fraction = gauge_v3_point.point_integrate_fraction(bob)
    charlie_point_fraction = gauge_v3_point.point_integrate_fraction(charlie)

    # Alice earned the same as Bob and charlie now
    d_alice = new_alice_point_fraction - alice_point_fraction
    d_bob = new_bob_point_fraction - bob_point_fraction
    assert d_alice == d_bob == charlie_point_fraction


    # alice withdraw all
    mock_lp_token.withdraw(LP_AMOUNT, {"from": alice})
    assert gauge_v3_point.point_integrate_fraction(alice) == 0
