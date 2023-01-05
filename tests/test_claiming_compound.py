import pytest
import brownie
import web3
from brownie.test import given, strategy
from brownie import Wei, reverts
import csv
import math

NULL = "0x0000000000000000000000000000000000000000"
BAYC_CAP = 10094000000000000000000
MAYC_CAP = 2042000000000000000000
BAKC_CAP = 856000000000000000000
BAYC_Q1 = 1678726800 - 1670864400
MAYC_Q1 = 1678726800 - 1670864400
BAKC_Q1 = 1678726800 - 1670864400
BAYC_DAILY_RATE = 16486750000000000000000000 // (MAYC_Q1 // 86400)
MAYC_DAILY_RATE = 6671000000000000000000000 // (MAYC_Q1 // 86400)
BAKC_DAILY_RATE = 1342250000000000000000000 // (BAKC_Q1 // 86400)

def get_payment_snapshot(matcher, p1, p2, p3, p4, ):
	return [
		matcher.payments(p1),
		matcher.payments(p2),
		matcher.payments(p3),
		matcher.payments(p4)
	]

def assert_expected_payment_both(matcher, p1, p2, p3, p4, reward_p, rewards_d, s):
	assert math.isclose(matcher.payments(p1) - s[0], (reward_p // 2 + rewards_d * 1 // 10) * 96 // 100)
	assert math.isclose(matcher.payments(p2) - s[1], (reward_p // 2 + rewards_d * 1 // 10) * 96 // 100)
	assert math.isclose(matcher.payments(p3) - s[2], rewards_d * 4 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(p4) - s[3], rewards_d * 4 // 10 * 96 // 100)

def assert_expected_payment_dog(matcher, p1, p2, p3, p4, rewards, s):
	assert math.isclose(matcher.payments(p1) - s[0], rewards * 1 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(p2) - s[1], rewards * 1 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(p3) - s[2], rewards * 4 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(p4) - s[3], rewards * 4 // 10 * 96 // 100)

def assert_expected_payment(matcher, p1, p2, rewards, s):
	assert math.isclose(matcher.payments(p1) - s[0], rewards // 2 * 96 // 100)
	assert math.isclose(matcher.payments(p2) - s[1], rewards // 2 * 96 // 100)

def test_claiming_from_bayc(matcher, ape, bayc, smooth, nft_guy, dog_guy, coin_guy, chain, compounder, ape_staking):
	ape.mint(coin_guy, '1000000 ether')
	ape.approve(matcher, 2 ** 256 - 1, {'from':coin_guy})
	ape.approve(compounder, 2 ** 256 - 1, {'from':coin_guy})
	bayc.mint(nft_guy, 10)
	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	matcher.depositNfts([1], [], [], {'from':nft_guy})
	matcher.depositApeToken([1,0,0], {'from':coin_guy})
	chain.sleep(86400)
	chain.mine()
	pre_smooth = ape.balanceOf(smooth)
	pending = ape_staking.pendingRewards(1, smooth, 1)
	matcher.batchClaimRewardsFromMatches([0], 0, {'from':nft_guy})
	assert math.isclose(matcher.payments(nft_guy), pending // 2 * 96 // 100)
	assert math.isclose(matcher.payments(coin_guy), pending // 2 * 96 // 100)
	assert math.isclose(ape.balanceOf(smooth) - pre_smooth, pending)
	chain.sleep(86400)
	chain.mine()
	pending_2 = ape_staking.pendingRewards(1, smooth, 1)
	pre_coin = ape.balanceOf(coin_guy)
	matcher.batchClaimRewardsFromMatches([0], 2, {'from':coin_guy})
	assert math.isclose(matcher.payments(nft_guy), (pending + pending_2) * 96 // 100 // 2)
	assert math.isclose(matcher.payments(coin_guy), 0)
	assert math.isclose(ape.balanceOf(coin_guy) - pre_coin, 0)
	assert math.isclose(ape.balanceOf(smooth) - matcher.fee() - pre_smooth, (pending + pending_2) * 96 // 100 // 2 )
	assert math.isclose(compounder.balanceOf(coin_guy),(pending + pending_2) * 96 // 100 // 2)