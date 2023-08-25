import json

from brownie import (
    MockCErc20,
    ERC20Impl,
    GaugeController,
    LiquidityGaugeV3,
    Minter,
    Treasury,
    RewardPolicyMaker,
    VotingEscrow,
    RewardHelper,
    accounts,
    history,
    ZERO_ADDRESS
)

from . import deployment_config as config

def development():
    token = ERC20Impl.deploy("FYLLO DAO Token", "FYO", 18, 100000, {"from": admin, "required_confs": confs})
    usdtest = ERC20Impl.deploy("Test usd token", "USDTEST", 18, 100000, {"from": admin, "required_confs": confs})
    cerc20 = MockCErc20.deploy("Test C usd Token", "cUSDTEST", 18, usdtest.address, {"from": admin, "required_confs": confs})

    deployments = {
        "FYO": token.address,
        "USDTEST": usdtest.address,
        "cUSDTEST": cerc20.address
    }
    if deployments_json is not None:
        with open(deployments_json, "w") as fp:
            json.dump(deployments, fp)
        print(f"Deployment addresses saved to {deployments_json}")

    voting_escrow = deploy_part_one(accounts[0])
    policy_reward = 10 ** 18
    gague_types = [
        ("Liquidity", 10 ** 18),
    ]

    pools = {
        "USDTEST": (cerc20.address, 10 ** 18, 10 ** 17, usdtest.address, 10 ** 15, 100),
    }
    deploy_part_two(accounts[0], token, voting_escrow, policy_reward, gague_types, pools)


def deploy_part_one(admin, token, confs=1, deployments_json=None):
    voting_escrow = VotingEscrow.deploy(
        token,
        "Vote-escrowed FYO",
        "veFYO",
        "veFYO_1.0.0",
        {"from": admin, "required_confs": confs},
    )
    deployments = {
        "VotingEscrow": voting_escrow.address,
    }
    if deployments_json is not None:
        with open(deployments_json, "w") as fp:
            json.dump(deployments, fp)
        print(f"Deployment addresses saved to {deployments_json}")

    return voting_escrow


def deploy_part_two(admin, token, voting_escrow, policy_reward, gague_types, pools, confs=1, deployments_json=None):
    print("Deploying Treasury...")
    treasury = Treasury.deploy(token, admin, {"from": admin, "required_confs": confs})

    print("Deploying RewardPolicyMaker...")
    policyMaker = RewardPolicyMaker.deploy(config.WEEK, admin, {"from": admin, "required_confs": confs})
    print("RewardPolicyMaker set next 10 epoch reward rate...")
    policyMaker.set_rewards_starting_at(policyMaker.current_epoch() + 1,
        [policy_reward, policy_reward, policy_reward, policy_reward, policy_reward,
         policy_reward, policy_reward, policy_reward, policy_reward, policy_reward],
         {"from": admin, "required_confs": confs})

    print("Deploying GaugeController...")
    gauge_controller = GaugeController.deploy(
        token, voting_escrow, {"from": admin, "required_confs": confs}
    )
    print("GaugeController add type...")
    for name, weight in gague_types:
        gauge_controller.add_type(name, weight, {"from": admin, "required_confs": confs})

    print("Deploying Minter...")
    minter = Minter.deploy(treasury.address, gauge_controller, {"from": admin, "required_confs": confs})
    print("Treasury set Minter...")
    treasury.set_minter(minter)

    deployments = {
        "VotingEscrow": voting_escrow.address,
        "GaugeController": gauge_controller.address,
        "Minter": minter.address,
        "LiquidityGaugeV3": {},
        "RewardPolicyMaker": policyMaker.address,
        "Treasury": treasury.address,
    }

    print("Deploying Gauge and add gauge to controller...")
    for name, (lp_token, point_rate, point_proportion, reward_token, reward_rate, weight) in pools.items():
        gauge = LiquidityGaugeV3.deploy("gauge-" + name, lp_token, minter, admin,
                policyMaker.address, point_rate, point_proportion, {"from": admin, "required_confs": confs})
        if reward_token != ZERO_ADDRESS:
            gauge.add_reward_token(reward_token, reward_rate, {"from": admin, "required_confs": confs})
        gauge_controller.add_gauge(gauge, 0, weight, {"from": admin, "required_confs": confs})
        deployments["LiquidityGaugeV3"][name] = gauge.address

    print(f"Deployment complete! Total gas used: {sum(i.gas_used for i in history)}")
    if deployments_json is not None:
        with open(deployments_json, "w") as fp:
            json.dump(deployments, fp)
        print(f"Deployment addresses saved to {deployments_json}")

def add_gauge(admin, name, minter, policyMaker, lp_token, point_rate, point_proportion, reward_token, reward_rate, weight, confs=1, deployments_json=None):
    minter_contract = Minter.at(minter)
    controller = GaugeController.at(minter_contract.controller())
    gauge = LiquidityGaugeV3.deploy("gauge-" + name, lp_token, minter, admin,
                policyMaker, point_rate, point_proportion, {"from": admin, "required_confs": confs})
    if reward_token != ZERO_ADDRESS:
        gauge.add_reward_token(reward_token, reward_rate, {"from": admin, "required_confs": confs})
    controller.add_gauge(gauge, 0, weight, {"from": admin, "required_confs": confs})

    if deployments_json is not None:
        with open(deployments_json, "r+") as fp:
            deployments = json.load(fp)
            fp.seek(0)
            deployments["LiquidityGaugeV3"][name] = gauge.address
            json.dump(deployments, fp)
        print(f"Deployment addresses saved to {deployments_json}")

    return gauge

def deploy_reward_helper(admin, deployments_json, confs=1):
    with open(deployments_json) as fp:
        deployments = json.load(fp)

    helper = RewardHelper.deploy(deployments["Minter"], {"from": admin, "required_confs": confs})

    with open(deployments_json, "r+") as fp:
        deployments = json.load(fp)
        fp.seek(0)
        deployments["RewardHelper"] = helper.address
        json.dump(deployments, fp)
    print(f"Deployment addresses saved to {deployments_json}")
