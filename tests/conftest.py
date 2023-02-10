import pytest
from brownie import Contract

BAYC_CAP = 10094000000000000000000
MAYC_CAP = 2042000000000000000000
BAKC_CAP = 856000000000000000000

@pytest.fixture(scope="module")
def admin(accounts):
    return accounts[0]

@pytest.fixture(scope="module")
def coin_guy(accounts):
    return accounts[1]

@pytest.fixture(scope="module")
def nft_guy(accounts):
    return accounts[2]

@pytest.fixture(scope="module")
def dog_guy(accounts):
    return accounts[5]

@pytest.fixture(scope="module")
def other_guy(accounts):
    return accounts[3]

@pytest.fixture(scope="module")
def some_guy(accounts):
    return accounts[6]

@pytest.fixture(scope="module")
def mix_guy(accounts):
    return accounts[4]

@pytest.fixture(scope="module")
def bayc(YugaNft, admin):
	return YugaNft.deploy({'from':admin})

@pytest.fixture(scope="module")
def mayc(YugaNft, admin):
	return YugaNft.deploy({'from':admin})

@pytest.fixture(scope="module")
def bakc(YugaNft, admin):
	return YugaNft.deploy({'from':admin})

@pytest.fixture(scope="module")
def ape(ApeCoin, admin):
	return ApeCoin.deploy({'from':admin})

@pytest.fixture(scope="module")
def ape_staking(ApeCoinStaking, admin, bayc, mayc, bakc, ape):
	staking =  ApeCoinStaking.deploy(ape, bayc, mayc, bakc, {'from':admin})
	ape.mint(staking, '100000000 ether', {'from':admin})
	staking.addTimeRange(0, 10500000000000000000000000, 1670864400, 1678726800,0,{'from':admin})
	staking.addTimeRange(0, 9000000000000000000000000, 1678726800, 1686675600,0,{'from':admin})
	staking.addTimeRange(0, 6000000000000000000000000, 1686675600, 1694538000,0,{'from':admin})
	staking.addTimeRange(0, 4500000000000000000000000, 1694538000, 1702400400,0,{'from':admin})

	staking.addTimeRange(1, 16486750000000000000000000, 1670864400, 1678726800,BAYC_CAP,{'from':admin})
	staking.addTimeRange(1, 14131500000000000000000000, 1678726800, 1686675600,BAYC_CAP,{'from':admin})
	staking.addTimeRange(1, 9421000000000000000000000, 1686675600, 1694538000,BAYC_CAP,{'from':admin})
	staking.addTimeRange(1, 7065750000000000000000000, 1694538000, 1702400400,BAYC_CAP,{'from':admin})

	staking.addTimeRange(2, 6671000000000000000000000, 1670864400, 1678726800,MAYC_CAP,{'from':admin})
	staking.addTimeRange(2, 5718000000000000000000000, 1678726800, 1686675600,MAYC_CAP,{'from':admin})
	staking.addTimeRange(2, 3812000000000000000000000, 1686675600, 1694538000,MAYC_CAP,{'from':admin})
	staking.addTimeRange(2, 2859000000000000000000000, 1694538000, 1702400400,MAYC_CAP,{'from':admin})

	staking.addTimeRange(3, 1342250000000000000000000, 1670864400, 1678726800,BAKC_CAP,{'from':admin})
	staking.addTimeRange(3, 1150500000000000000000000, 1678726800, 1686675600,BAKC_CAP,{'from':admin})
	staking.addTimeRange(3, 767000000000000000000000, 1686675600, 1694538000,BAKC_CAP,{'from':admin})
	staking.addTimeRange(3, 575250000000000000000000, 1694538000, 1702400400,BAKC_CAP,{'from':admin})
	return staking

@pytest.fixture(scope="module")
def compounder(ApeStakingCompounder, ape, ape_staking, admin):
	comp = ApeStakingCompounder.deploy(ape_staking, ape, {'from':admin})
	return comp

@pytest.fixture(scope="module")
def flash_manager(FlashloanManager, admin):
	return FlashloanManager.deploy({'from':admin})

@pytest.fixture(scope="module")
def matcher(ApeMatcher, SmoothOperator, admin, bayc, mayc, bakc, ape, ape_staking, compounder, flash_manager, chain):
	ma =  ApeMatcher.deploy(bayc, mayc, bakc, ape, ape_staking,{'from':admin})
	ope =  SmoothOperator.deploy(ma, bayc, mayc, bakc, ape, ape_staking,{'from':admin})
	ope.updateFlashloanProxy(flash_manager, {'from':admin})
	ma.init(ope, compounder, {'from':admin})
	ma.updateWeights([500,500,0,0], [500,500,0,0], [100,100,400,400], {'from':admin})
	compounder.setMatcher(ma,{'from':admin})
	compounder.setSmooth(ope,{'from':admin})
	chain.sleep(86400)
	chain.mine()
	return ma


@pytest.fixture(scope="module")
def smooth(SmoothOperator, admin, bayc, mayc, bakc, ape, ape_staking, matcher):
	ope = SmoothOperator.at(matcher.smoothOperator())
	return ope

@pytest.fixture(scope="module")
def split(MockSplit, admin, ):
	return MockSplit.deploy({'from':admin})

@pytest.fixture(scope="module")
def redeemer(TokenRedeemer,bayc, ape, admin):
	return TokenRedeemer.deploy(bayc, ape, {'from':admin})

@pytest.fixture(scope="module")
def flash_redeemer(FLTokenRedeemer, redeemer, ape, admin):
	return FLTokenRedeemer.deploy(redeemer, ape, {'from':admin})