import brownie
from brownie import ZERO_ADDRESS, chain
from brownie.test import strategy

from tests.conftest import approx

WEEK = 7 * 86400

class StateMachine:
    """
    Validate that eventually users claim almost all rewards (except for dust)
    """

    st_account = strategy("address", length=5)
    st_value = strategy("uint64", min_value=10 ** 10)
    st_time = strategy("uint", max_value=365 * 86400)
    st_reward = strategy("uint64", min_value=10 ** 10)

    def __init__(self, accounts, gauge_v3, coin_deposit, mock_lp_token, coin_reward):
        self.accounts = accounts
        self.deposit_token = coin_deposit
        self.token = mock_lp_token
        self.liquidity_gauge = gauge_v3
        self.coin_reward = coin_reward


    def setup(self):
        self.balances = {i: 0 for i in self.accounts}
        self.rewards_total = 0
        self.total_balances = 0
        self.flag = False
        self.reward_start = 0
        self.reward_rate = 0

    def rule_deposit(self, st_account, st_value):
        """
        Make a deposit into the `LiquidityGauge` contract.

        Because of the upper bound of `st_value` relative to the initial account
        balances, this rule should never fail.
        """
        balance = self.deposit_token.balanceOf(st_account)

        self.token.deposit(st_value, {"from": st_account})
        self.balances[st_account] += st_value
        self.total_balances += st_value

        assert self.deposit_token.balanceOf(st_account) == balance - st_value

    def rule_set_reward(self, st_reward):
        """
        Add rewards only if at least someone has deposits
        """
        if self.total_balances > 0:
            if not self.flag:
                self.liquidity_gauge.add_reward_token(self.coin_reward, st_reward)
                self.reward_start = chain.time()
                self.reward_rate = st_reward
                self.flag = True

    def rule_withdraw(self, st_account, st_value):
        """
        Attempt to withdraw from the `LiquidityGauge` contract.
        Don't withdraw if this leads to empty contract (rewards won't go to anyone)
        """
        if st_value >= self.total_balances:
            return

        if self.balances[st_account] < st_value:
            # fail path - insufficient balance
            with brownie.reverts():
                self.token.withdraw(st_value, {"from": st_account})
            return

        # success path
        balance = self.deposit_token.balanceOf(st_account)
        self.token.withdraw(st_value, {"from": st_account})
        self.balances[st_account] -= st_value
        self.total_balances -= st_value

        assert self.deposit_token.balanceOf(st_account) == balance + st_value

    def rule_advance_time(self, st_time):
        """
        Advance the clock.
        """
        chain.sleep(st_time)

    def rule_checkpoint(self, st_account):
        """
        Create a new user checkpoint.
        """
        self.liquidity_gauge.user_checkpoint(st_account, {"from": st_account})

    def invariant_balances(self):
        """
        Validate expected balances against actual balances.
        """
        for account, balance in self.balances.items():
            assert self.liquidity_gauge.balanceOf(account) == balance

    def invariant_total_supply(self):
        """
        Validate expected total supply against actual total supply.
        """
        assert self.liquidity_gauge.totalSupply() == sum(self.balances.values())

    def teardown(self):
        """
        Travel far enough in future for all rewards to be distributed (1 week)
        and claim all
        """
        chain.sleep(2 * 7 * 86400)

        start_time = chain.time()
        dt = 0
        if self.reward_start != 0:
            dt = start_time - self.reward_start + 20 # dt add 20 seconds
            self.coin_reward._mint_for_testing(self.liquidity_gauge, self.reward_rate * dt)
            self.rewards_total += self.reward_rate * dt

        rewards_claimed = 0
        for act in self.accounts:
            self.liquidity_gauge.claim_rewards({"from": act})
            rewards_claimed += self.coin_reward.balanceOf(act)

        if self.rewards_total > 0:  # Otherwise we may have 0 claimed
            dt1 = chain.time() - start_time
            precision = max((dt - dt1) * self.reward_rate, 1e-10)
            assert approx(rewards_claimed, self.rewards_total, precision)


def test_state_machine(
    state_machine,
    accounts,
    gauge_v3,
    coin_deposit,
    mock_lp_token,
    coin_reward,
    no_call_coverage,
):
    # fund accounts to be used in the test
    for acct in accounts[0:5]:
        coin_deposit.mint(acct, 10 ** 21, {"from": accounts[0]})

    # approve liquidity_gauge from the funded accounts
    for acct in accounts[:5]:
        coin_deposit.approve(mock_lp_token, 2 ** 256 - 1, {"from": acct})

    # because this is a simple state machine, we use more steps than normal
    settings = {"stateful_step_count": 25, "max_examples": 30}

    state_machine(
        StateMachine,
        accounts[:5],
        gauge_v3,
        coin_deposit,
        mock_lp_token,
        coin_reward,
        settings=settings,
    )
