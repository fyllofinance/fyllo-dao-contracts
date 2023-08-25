import pytest
from brownie import (
    compile_source,
    convert,
)
from brownie_tokens import ERC20

YEAR = 365 * 86400


def approx(a, b, precision=1e-10):
    if a == b == 0:
        return True
    return 2 * abs(a - b) / (a + b) <= precision


def pack_values(values):
    packed = b"".join(i.to_bytes(1, "big") for i in values)
    padded = packed + bytes(32 - len(values))
    return padded


@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass


# account aliases


@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def charlie(accounts):
    yield accounts[2]


@pytest.fixture(scope="session")
def receiver(accounts):
    yield accounts.at("0x0000000000000000000000000000000000031337", True)


# core contracts


@pytest.fixture(scope="module")
def token(ERC20Impl, accounts):
    yield ERC20Impl.deploy("Fyllo DAO Token", "FYOTT", 18, 0, {"from": accounts[0]})


@pytest.fixture(scope="module")
def voting_escrow(VotingEscrow, accounts, token):
    yield VotingEscrow.deploy(
        token, "Voting-escrowed FYO", "veFYO", "veFYO_0.99", {"from": accounts[0]}
    )


@pytest.fixture(scope="module")
def gauge_controller(GaugeController, accounts, token, voting_escrow):
    yield GaugeController.deploy(token, voting_escrow, {"from": accounts[0]})


@pytest.fixture(scope="module")
def minter(Treasury, Minter, accounts, gauge_controller, token):
    treasury = Treasury.deploy(token, accounts[0], {"from": accounts[0]})
    token.mint(treasury, 100_000_000 * 10 ** 18, {"from": accounts[0]})

    minter = Minter.deploy(treasury, gauge_controller, {"from": accounts[0]})
    treasury.set_minter(minter)

    yield minter

@pytest.fixture(scope="module")
def reward_policy_maker(RewardPolicyMaker, accounts):
    reward = 100 * 10 ** 18
    contract = RewardPolicyMaker.deploy(604800, accounts[0], {"from": accounts[0]})
    contract.set_rewards_starting_at(contract.current_epoch() + 1, [reward, reward, reward, reward, reward, reward, reward, reward, reward, reward])
    contract.set_rewards_starting_at(contract.current_epoch() + 11, [reward, reward, reward, reward, reward, reward, reward, reward, reward, reward])
    yield contract

@pytest.fixture(scope="module")
def coin_reward():
    yield ERC20("YFIIIIII Funance", "YFIIIIII", 18)


@pytest.fixture(scope="module")
def gauge_v3(LiquidityGaugeV3, alice, mock_lp_token, minter, reward_policy_maker):
    gauge_name = mock_lp_token.symbol() + "-gauge"
    gauge = LiquidityGaugeV3.deploy(gauge_name, mock_lp_token, minter, alice,
            reward_policy_maker, 0, 0, {"from": alice})
    mock_lp_token.setGauge(gauge, {"from": alice})
    yield gauge

@pytest.fixture(scope="module")
def gauge_v3_point(LiquidityGaugeV3, alice, mock_lp_token, minter, reward_policy_maker):
    gauge_name = mock_lp_token.symbol() + "-gauge"
    gauge = LiquidityGaugeV3.deploy(gauge_name, mock_lp_token, minter, alice,
            reward_policy_maker, 10000 * 10 ** 18, 10 ** 17, {"from": alice})
    mock_lp_token.setGauge(gauge, {"from": alice})
    yield gauge

@pytest.fixture(scope="module")
def three_gauges(LiquidityGaugeV3, accounts, mock_lp_token_A, mock_lp_token_B, mock_lp_token_C, minter, reward_policy_maker):
    contracts = []

    gauge_nameA = mock_lp_token_A.symbol() + "-gauge"
    contractA = LiquidityGaugeV3.deploy(gauge_nameA, mock_lp_token_A, minter, accounts[0], reward_policy_maker,
        0, 0, {"from": accounts[0]})
    mock_lp_token_A.setGauge(contractA, {"from": accounts[0]})
    contracts.append(contractA)

    gauge_nameB = mock_lp_token_B.symbol() + "-gauge"
    contractB = LiquidityGaugeV3.deploy(gauge_nameB, mock_lp_token_B, minter, accounts[0], reward_policy_maker,
        0, 0, {"from": accounts[0]})
    mock_lp_token_B.setGauge(contractB, {"from": accounts[0]})
    contracts.append(contractB)

    gauge_name = mock_lp_token_C.symbol() + "-gauge"
    contractC = LiquidityGaugeV3.deploy(gauge_name, mock_lp_token_C, minter, accounts[0], reward_policy_maker,
        0, 0, {"from": accounts[0]})
    mock_lp_token_C.setGauge(contractC, {"from": accounts[0]})
    contracts.append(contractC)

    yield contracts


# testing contracts

@pytest.fixture(scope="module")
def coin_deposit(ERC20Impl, accounts):
    yield ERC20Impl.deploy("Coin deposit", "USD", 18, 0, {"from": accounts[0]})

@pytest.fixture(scope="module")
def coin_a():
    yield ERC20("Coin A", "USDA", 18)


@pytest.fixture(scope="module")
def coin_b():
    yield ERC20("Coin B", "USDB", 18)


@pytest.fixture(scope="module")
def coin_c():
    yield ERC20("Coin C", "mWBTC", 8)


@pytest.fixture(scope="module")
def mock_lp_token(MockCErc20, coin_deposit, accounts):  # Not using the actual Curve contract
    yield MockCErc20.deploy("Fyllo C deposit token", "cUSD", 18, coin_deposit, {"from": accounts[0]})

@pytest.fixture(scope="module")
def mock_lp_token_A(MockCErc20, coin_a, accounts):  # Not using the actual Curve contract
    yield MockCErc20.deploy("Fyllo C A token", "cUSDA", 18, coin_a, {"from": accounts[0]})

@pytest.fixture(scope="module")
def mock_lp_token_B(MockCErc20, coin_b, accounts):  # Not using the actual Curve contract
    yield MockCErc20.deploy("Fyllo C B token", "cUSDB", 18, coin_b, {"from": accounts[0]})

@pytest.fixture(scope="module")
def mock_lp_token_C(MockCErc20, coin_c, accounts):  # Not using the actual Curve contract
    yield MockCErc20.deploy("Fyllo C C token", "cWBTC", 18, coin_c, {"from": accounts[0]})

@pytest.fixture(scope="module")
def gauge_for_mock_v2(LiquidityGaugeV3, alice, mock_lp_token_v2, minter, reward_policy_maker):
    gauge_name = mock_lp_token_v2.symbol() + "-gauge"
    gauge = LiquidityGaugeV3.deploy(gauge_name, mock_lp_token_v2, minter, alice,
            reward_policy_maker, 0, 0, {"from": alice})
    yield gauge

@pytest.fixture(scope="module")
def mock_lp_token_v2(MockCErc20V2, coin_deposit, accounts, gauge_controller):  # Not using the actual Curve contract
    cerc20v2 = MockCErc20V2.deploy("Fyllo C deposit token", "cUSD", 18, coin_deposit, {"from": accounts[0]})
    cerc20v2.setController(gauge_controller)
    yield cerc20v2

@pytest.fixture(scope="module")
def reward_helper(RewardHelper, minter, accounts):
    yield RewardHelper.deploy(minter, {"from": accounts[0]})
