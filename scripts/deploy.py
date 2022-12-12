import brownie
from brownie import Wei, accounts, ApeMatcher, SmoothOperator

APE_STAKING = '0x5954aB967Bc958940b7EB73ee84797Dc8a2AFbb9'
ALPHA = '0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D'
BETA = '0x60E4d786628Fea6478F785A6d7e704777c86a7c6'
GAMMA = '0xba30E5F9Bb24caa003E9f2f0497Ad287FDF95623'
APE = '0x4d224452801ACEd8B2F0aebE155379bb5D594381'

def deploy():
	deployer = accounts.load('ape_matcher_dep', '\0')

	matcher = ApeMatcher.deploy(ALPHA, BETA, GAMMA, APE, APE_STAKING,  {'from':deployer}, publish_source=True)
	ope =  SmoothOperator.deploy(matcher, ALPHA, BETA, GAMMA, APE, APE_STAKING,{'from':deployer}, publish_source=True)
	matcher.setOperator(ope, {'from':deployer})