import brownie
from brownie import Wei, accounts, ApeMatcher, SmoothOperator, ApeMatcherHelper, ApeCoin,  YugaNft, ApeCoinStaking

APE_STAKING = '0x5954aB967Bc958940b7EB73ee84797Dc8a2AFbb9'
ALPHA = '0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D'
BETA = '0x60E4d786628Fea6478F785A6d7e704777c86a7c6'
GAMMA = '0xba30E5F9Bb24caa003E9f2f0497Ad287FDF95623'
APE = '0x4d224452801ACEd8B2F0aebE155379bb5D594381'

BAYC_CAP = 10094000000000000000000
MAYC_CAP = 2042000000000000000000
BAKC_CAP = 856000000000000000000

def deploy():
	deployer = accounts.load('ape_matcher_dep', '\0')

	matcher = ApeMatcher.deploy(ALPHA, BETA, GAMMA, APE, APE_STAKING,  {'from':deployer}, publish_source=True)
	ope =  SmoothOperator.deploy(matcher, ALPHA, BETA, GAMMA, APE, APE_STAKING,{'from':deployer}, publish_source=True)
	matcher.setOperator(ope, {'from':deployer})
	helper = ApeMatcherHelper.deploy(APE_STAKING, ALPHA, BETA, GAMMA, APE, matcher, ope, {'from':deployer}, publish_source=True)

	print(f'matcher: {matcher.address}')
	print(f'smooth: {ope.address}')
	print(f'helper: {helper.address}')

def deploy_go():
	deployer = accounts.load('ape_matcher_dep', '\0')

	ape = ApeCoin.deploy({'from':deployer}, publish_source=True)
	alpha = YugaNft.deploy({'from':deployer}, publish_source=True)
	beta = YugaNft.deploy({'from':deployer}, publish_source=True)
	gamma = YugaNft.deploy({'from':deployer}, publish_source=True)

	ape_staking = ApeCoinStaking.deploy(ape, alpha, beta, gamma, {'from':deployer}, publish_source=True)
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

	matcher = ApeMatcher.deploy(alpha, beta, gamma, ape, APE_STAKING,  {'from':deployer}, publish_source=True)
	ope =  SmoothOperator.deploy(matcher, alpha, beta, gamma, ape, APE_STAKING,{'from':deployer}, publish_source=True)
	matcher.setOperator(ope, {'from':deployer})
	helper = ApeMatcherHelper.deploy(APE_STAKING, alpha, beta, gamma, ape, matcher, ope, {'from':deployer}, publish_source=True)

	print(f'alpha: {alpha.address}')
	print(f'beta: {beta.address}')
	print(f'gamma: {gamma.address}')
	print(f'ape: {ape.address}')
	print(f'ape staker: {ape_staking.address}')

	print(f'matcher: {matcher.address}')
	print(f'smooth: {ope.address}')
	print(f'helper: {helper.address}')