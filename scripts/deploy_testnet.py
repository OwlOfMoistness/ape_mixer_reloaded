import brownie
from brownie import Wei, accounts, ApeMatcher, SmoothOperator, ApeMatcherHelper, ApeCoin,  YugaNft, ApeCoinStaking

BAYC_CAP = 10094000000000000000000
MAYC_CAP = 2042000000000000000000
BAKC_CAP = 856000000000000000000


def main():
	deployer = accounts.load('insert_name', '\0')

	ape = ApeCoin.deploy({'from':deployer}, publish_source=True)
	alpha = YugaNft.deploy({'from':deployer}, publish_source=True)
	beta = YugaNft.deploy({'from':deployer}, publish_source=False)
	gamma = YugaNft.deploy({'from':deployer}, publish_source=False)


	ape_staking = ApeCoinStaking.deploy(ape, alpha, beta, gamma, {'from':deployer}, publish_source=False)
	ape.mint(ape_staking, '100000000 ether', {'from':deployer})
	ape_staking.addTimeRange(0, 10500000000000000000000000, 1670864400, 1678726800,0,{'from':deployer})
	ape_staking.addTimeRange(0, 9000000000000000000000000, 1678726800, 1686675600,0,{'from':deployer})
	ape_staking.addTimeRange(0, 6000000000000000000000000, 1686675600, 1694538000,0,{'from':deployer})
	ape_staking.addTimeRange(0, 4500000000000000000000000, 1694538000, 1702400400,0,{'from':deployer})

	ape_staking.addTimeRange(1, 16486750000000000000000000, 1670864400, 1678726800,BAYC_CAP,{'from':deployer})
	ape_staking.addTimeRange(1, 14131500000000000000000000, 1678726800, 1686675600,BAYC_CAP,{'from':deployer})
	ape_staking.addTimeRange(1, 9421000000000000000000000, 1686675600, 1694538000,BAYC_CAP,{'from':deployer})
	ape_staking.addTimeRange(1, 7065750000000000000000000, 1694538000, 1702400400,BAYC_CAP,{'from':deployer})

	ape_staking.addTimeRange(2, 6671000000000000000000000, 1670864400, 1678726800,MAYC_CAP,{'from':deployer})
	ape_staking.addTimeRange(2, 5718000000000000000000000, 1678726800, 1686675600,MAYC_CAP,{'from':deployer})
	ape_staking.addTimeRange(2, 3812000000000000000000000, 1686675600, 1694538000,MAYC_CAP,{'from':deployer})
	ape_staking.addTimeRange(2, 2859000000000000000000000, 1694538000, 1702400400,MAYC_CAP,{'from':deployer})

	ape_staking.addTimeRange(3, 1342250000000000000000000, 1670864400, 1678726800,BAKC_CAP,{'from':deployer})
	ape_staking.addTimeRange(3, 1150500000000000000000000, 1678726800, 1686675600,BAKC_CAP,{'from':deployer})
	ape_staking.addTimeRange(3, 767000000000000000000000, 1686675600, 1694538000,BAKC_CAP,{'from':deployer})
	ape_staking.addTimeRange(3, 575250000000000000000000, 1694538000, 1702400400,BAKC_CAP,{'from':deployer})

	matcher = ApeMatcher.deploy(alpha, beta, gamma, ape, ape_staking,  {'from':deployer}, publish_source=True)
	ope =  SmoothOperator.deploy(matcher, alpha, beta, gamma, ape, ape_staking,{'from':deployer}, publish_source=True)
	ope =  SmoothOperator.at('0xB46cb1F47173b7962D2DF3D7346cCe6fD3295F82')
	helper = ApeMatcherHelper.deploy(ape_staking, alpha, beta, gamma, ape, matcher, ope, {'from':deployer}, publish_source=True)
	matcher.setOperator(ope, {'from':deployer, 'required_confs':0})
	matcher.updateWeights([500,500,0,0], [100,100,400,400], {'from':deployer, 'required_confs':0})

	print(f'alpha: {alpha.address}')
	print(f'beta: {beta.address}')
	print(f'gamma: {gamma.address}')
	print(f'ape: {ape.address}')
	print(f'ape staker: {ape_staking.address}')

	print(f'matcher: {matcher.address}')
	print(f'smooth: {ope.address}')
	print(f'helper: {helper.address}')