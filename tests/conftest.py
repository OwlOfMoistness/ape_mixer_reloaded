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
def other_guy(accounts):
    return accounts[3]

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
	ape.mint(admin, '100000000 ether', {'from':admin})
	staking =  ApeCoinStaking.deploy(ape, bayc, mayc, bakc, {'from':admin})
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
def matcher(ApeMatcher, admin, bayc, mayc, bakc, ape, ape_staking):
	return ApeMatcher.deploy(bayc, mayc, bakc, ape, ape_staking,{'from':admin})

@pytest.fixture(scope="module")
def matcher(ApeMatcher, admin, bayc, mayc, bakc, ape, ape_staking):
	return ApeMatcher.deploy(bayc, mayc, bakc, ape, ape_staking,{'from':admin})

@pytest.fixture(scope="module")
def smooth(SmoothOperator, admin, bayc, mayc, bakc, ape, ape_staking, matcher):
	ope =  SmoothOperator.deploy(matcher, bayc, mayc, bakc, ape, ape_staking,{'from':admin})
	matcher.setOperator(ope, {'from':admin})
	return ope

