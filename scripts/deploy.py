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

	matcher = ApeMatcher.deploy(ALPHA, BETA, GAMMA, APE, APE_STAKING,  {'from':deployer}, publish_source=False)
	ope =  SmoothOperator.deploy(matcher, ALPHA, BETA, GAMMA, APE, APE_STAKING,{'from':deployer}, publish_source=False)
	matcher.setOperator(ope, {'from':deployer})
	helper = ApeMatcherHelper.deploy(APE_STAKING, ALPHA, BETA, GAMMA, APE, matcher, ope, {'from':deployer}, publish_source=False)

	print(f'matcher: {matcher.address}')
	print(f'smooth: {ope.address}')
	print(f'helper: {helper.address}')

def deploy_go():
	deployer = accounts.load('owl_eth', '\0')

	# ape = ApeCoin.deploy({'from':deployer}, publish_source=False)
	# alpha = YugaNft.deploy({'from':deployer}, publish_source=False)
	# beta = YugaNft.deploy({'from':deployer}, publish_source=False)
	# gamma = YugaNft.deploy({'from':deployer}, publish_source=False)

	ape = ApeCoin.at('0xa79279E4A3284752445372E590bAc77a2Fd42541')
	alpha = YugaNft.at('0x2a1c47a673Afb2315E5f15A5F79c299Def3D738D')
	beta = YugaNft.at('0x5E27567ff29F54E21301e1b181216e75Def4D1f1')
	gamma = YugaNft.at('0xF91e97f34f9abc9B881fa174fC5d41D2824B3bb8')

	# ape_staking = ApeCoinStaking.deploy(ape, alpha, beta, gamma, {'from':deployer}, publish_source=False)
	ape_staking = ApeCoinStaking.at('0x67C71B2317984e063C309D60270B312287bcFd24')
	# ape.mint(ape_staking, '100000000 ether', {'from':deployer})
	# ape_staking.addTimeRange(0, 10500000000000000000000000, 1670864400, 1678726800,0,{'from':deployer})
	# ape_staking.addTimeRange(0, 9000000000000000000000000, 1678726800, 1686675600,0,{'from':deployer})
	# ape_staking.addTimeRange(0, 6000000000000000000000000, 1686675600, 1694538000,0,{'from':deployer})
	# ape_staking.addTimeRange(0, 4500000000000000000000000, 1694538000, 1702400400,0,{'from':deployer})

	# ape_staking.addTimeRange(1, 16486750000000000000000000, 1670864400, 1678726800,BAYC_CAP,{'from':deployer})
	# ape_staking.addTimeRange(1, 14131500000000000000000000, 1678726800, 1686675600,BAYC_CAP,{'from':deployer})
	# ape_staking.addTimeRange(1, 9421000000000000000000000, 1686675600, 1694538000,BAYC_CAP,{'from':deployer})
	# ape_staking.addTimeRange(1, 7065750000000000000000000, 1694538000, 1702400400,BAYC_CAP,{'from':deployer})

	# ape_staking.addTimeRange(2, 6671000000000000000000000, 1670864400, 1678726800,MAYC_CAP,{'from':deployer})
	# ape_staking.addTimeRange(2, 5718000000000000000000000, 1678726800, 1686675600,MAYC_CAP,{'from':deployer})
	# ape_staking.addTimeRange(2, 3812000000000000000000000, 1686675600, 1694538000,MAYC_CAP,{'from':deployer})
	# ape_staking.addTimeRange(2, 2859000000000000000000000, 1694538000, 1702400400,MAYC_CAP,{'from':deployer})

	# ape_staking.addTimeRange(3, 1342250000000000000000000, 1670864400, 1678726800,BAKC_CAP,{'from':deployer})
	# ape_staking.addTimeRange(3, 1150500000000000000000000, 1678726800, 1686675600,BAKC_CAP,{'from':deployer})
	# ape_staking.addTimeRange(3, 767000000000000000000000, 1686675600, 1694538000,BAKC_CAP,{'from':deployer})
	# ape_staking.addTimeRange(3, 575250000000000000000000, 1694538000, 1702400400,BAKC_CAP,{'from':deployer})

	# matcher = ApeMatcher.deploy(alpha, beta, gamma, ape, ape_staking,  {'from':deployer}, publish_source=True)
	matcher = ApeMatcher.at('0x71e9016ECC772FB54f51b2d3D955C2931E2044D2')
	# ope =  SmoothOperator.deploy(matcher, alpha, beta, gamma, ape, ape_staking,{'from':deployer}, publish_source=True)
	ope =  SmoothOperator.at('0xB46cb1F47173b7962D2DF3D7346cCe6fD3295F82')
	# SmoothOperator.publish_source(ope)
	helper = ApeMatcherHelper.deploy(ape_staking, alpha, beta, gamma, ape, matcher, ope, {'from':deployer}, publish_source=True)
	# matcher.setOperator(ope, {'from':deployer, 'required_confs':0})
	# matcher.updateWeights([500,500,0,0], [100,100,400,400], {'from':deployer, 'required_confs':0})

	print(f'alpha: {alpha.address}')
	print(f'beta: {beta.address}')
	print(f'gamma: {gamma.address}')
	print(f'ape: {ape.address}')
	print(f'ape staker: {ape_staking.address}')

	print(f'matcher: {matcher.address}')
	print(f'smooth: {ope.address}')
	print(f'helper: {helper.address}')