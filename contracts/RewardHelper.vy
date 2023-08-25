# @version 0.2.12
"""
@title Reward Helper
@author Fyllo Finance
@license MIT
@notice Help user claim rewards.
"""

interface Controller:
    def gauge_types(addr: address) -> int128: view

interface Minter:
    def controller() -> address: view
    def mint_for(gauge_addr: address, _for: address): nonpayable

interface LiquidityGauge:
    def lp_token() -> address: view
    def claim_rewards(_addr: address): nonpayable


controller: public(address)
minter: public(address)


@external
def __init__(_minter: address):
    self.controller = Minter(_minter).controller()
    self.minter = _minter

@external
def claim_rewards_for(_addr: address, _gauges: address[10]):
    """
    @notice Claim available reward tokens for `_addr`
    @param _addr Address to claim for
    @param _gauges Gauge addresses to claim rewards
    """
    assert _addr != ZERO_ADDRESS, "invalid parameter"

    controller: address = self.controller
    minter: address = self.minter
    for gauge in _gauges:
        # check gauge is added
        if gauge != ZERO_ADDRESS and Controller(controller).gauge_types(gauge) >= 0:
            Minter(minter).mint_for(gauge, _addr)
            LiquidityGauge(gauge).claim_rewards(_addr)


