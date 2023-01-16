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

def test_claiming_from_bayc(matcher, ape, bayc, smooth, nft_guy, dog_guy, coin_guy, chain, ape_staking, compounder, admin):
	ape.mint(coin_guy, '1000000 ether')
	ape.approve(compounder, 2 ** 256 - 1, {'from':coin_guy})
	bayc.mint(nft_guy, 10)
	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	compounder.deposit('1000000 ether', {'from':coin_guy})
	matcher.depositNfts([1], [], [], {'from':nft_guy})
	to_sleep = 0 if chain.time() > 1670864400 else 1670864400 - chain.time()
	chain.sleep(to_sleep)
	chain.mine()
	chain.sleep(86400)
	chain.mine()
	bayc_rewards =  ape_staking.pendingRewards(1, matcher, 1)
	pre_smooth = ape.balanceOf(smooth)
	matcher.batchClaimRewardsFromMatches([0], 0, {'from':nft_guy})
	assert math.isclose(matcher.payments(nft_guy), bayc_rewards // 2 * 96 // 100)
	assert math.isclose(matcher.payments(compounder), bayc_rewards // 2 * 96 // 100)
	assert math.isclose(ape.balanceOf(smooth) - pre_smooth, bayc_rewards)
	chain.sleep(86400)
	chain.mine()
	bayc_rewards_2 =  ape_staking.pendingRewards(1, matcher, 1)
	pre_coin = compounder.liquid()
	pool0_rewards = ape_staking.pendingRewards(0, compounder, 0)
	compounder.claimNftStaking([0], {'from':admin})
	assert math.isclose(matcher.payments(nft_guy), (bayc_rewards + bayc_rewards_2) // 2 * 96 // 100)
	assert math.isclose(matcher.payments(compounder), 0)
	assert math.isclose(compounder.liquid() - pre_coin - pool0_rewards, (bayc_rewards + bayc_rewards_2) // 2 * 96 // 100)
	assert math.isclose(ape.balanceOf(smooth) - matcher.fee() - pre_smooth, (bayc_rewards + bayc_rewards_2) // 2 * 96 // 100 )

def test_claiming_from_mayc(matcher, ape, mayc, smooth, nft_guy, dog_guy, other_guy, coin_guy,chain, ape_staking, compounder, admin):
	mayc.mint(dog_guy, 10)
	mayc.setApprovalForAll(matcher, True, {'from':dog_guy})
	matcher.depositNfts([], [1], [], {'from':dog_guy})
	chain.sleep(86400)
	chain.mine()
	pre_nft = ape.balanceOf(dog_guy)
	pre_smooth = ape.balanceOf(smooth)
	mayc_rewards =  ape_staking.pendingRewards(2, matcher, 1)
	with reverts('!mtch'):
		matcher.batchClaimRewardsFromMatches([0], 0, {'from':dog_guy})
	matcher.batchClaimRewardsFromMatches([1], 0, {'from':dog_guy})
	assert math.isclose(matcher.payments(dog_guy), mayc_rewards // 2 * 96 // 100)
	assert math.isclose(matcher.payments(compounder), mayc_rewards // 2 * 96 // 100)
	assert math.isclose(ape.balanceOf(smooth) - pre_smooth, mayc_rewards)
	chain.sleep(86400)
	chain.mine()
	mayc_rewards_2 =  ape_staking.pendingRewards(2, matcher, 1)
	pre_coin = compounder.liquid()
	pool0_rewards = ape_staking.pendingRewards(0, compounder, 0)
	compounder.claimNftStaking([1], {'from':admin})
	assert math.isclose(matcher.payments(dog_guy), (mayc_rewards + mayc_rewards_2) // 2 * 96 // 100)
	assert math.isclose(matcher.payments(compounder), 0)
	assert math.isclose(compounder.liquid() - pre_coin - pool0_rewards, (mayc_rewards + mayc_rewards_2) // 2 * 96 // 100)
	assert math.isclose(ape.balanceOf(smooth) - pre_smooth , (mayc_rewards + mayc_rewards_2) // 2 * 104 // 100)

	assert ape.balanceOf(smooth) - matcher.fee() == matcher.payments(dog_guy) + matcher.payments(compounder) + matcher.payments(nft_guy) + matcher.payments(coin_guy)

def test_claiming_bakc_all_unique(matcher, ape, bakc, smooth, mix_guy, dog_guy, some_guy, chain, ape_staking, compounder, admin):
# pendingRewards
	bakc.mint(mix_guy, 10)
	bakc.setApprovalForAll(matcher, True, {'from':mix_guy})
	with reverts('!mtch'):
		matcher.batchClaimRewardsFromMatches([0], 0, {'from':some_guy})
	matcher.depositNfts([], [], [1], {'from':mix_guy})
	(self, dogless, ids, pO, dO) = matcher.matches(1)
	assert (dogless & 1, ids, pO, dO, self) == (0, (1 << 48) +  1, dog_guy, mix_guy, False)
	chain.sleep(86400)
	chain.mine()
	
	bakc_rewards = ape_staking.pendingRewards(3, matcher, 1)
	pre_smooth = ape.balanceOf(smooth)
	dog_payment = matcher.payments(dog_guy)
	c_payment = matcher.payments(compounder)
	matcher.batchClaimRewardsFromMatches([1], 0, {'from':mix_guy})
	assert math.isclose(ape.balanceOf(smooth) - pre_smooth, bakc_rewards)
	assert math.isclose(matcher.payments(mix_guy), bakc_rewards * 4 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(compounder), bakc_rewards * 4 // 10 * 96 // 100 + bakc_rewards * 1 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(dog_guy) - dog_payment, bakc_rewards * 1 // 10 * 96 // 100)
	chain.sleep(86400)
	chain.mine()
	bakc_rewards_2 = ape_staking.pendingRewards(3, matcher, 1)
	matcher.batchClaimRewardsFromMatches([1], 1, {'from':mix_guy})
	assert matcher.payments(mix_guy)== 0
	assert math.isclose(ape.balanceOf(mix_guy), (bakc_rewards + bakc_rewards_2) * 4 // 10 * 96 // 100)
	assert math.isclose(matcher.payments(compounder), (bakc_rewards + bakc_rewards_2) * 4 // 10 * 96 // 100 + (bakc_rewards + bakc_rewards_2) // 10 * 96 // 100)
	assert math.isclose(matcher.payments(dog_guy) - dog_payment, (bakc_rewards + bakc_rewards_2) // 10 * 96 // 100)

	pre_dog = ape.balanceOf(dog_guy)
	pre_c = compounder.liquid()
	mayc_rewards = ape_staking.pendingRewards(2, matcher, 1)
	pool0_rewards = ape_staking.pendingRewards(0, compounder, 0)
	matcher.batchClaimRewardsFromMatches([1], 1, {'from':dog_guy})
	assert matcher.payments(dog_guy)== 0
	assert math.isclose(ape.balanceOf(dog_guy) - pre_dog, dog_payment + (bakc_rewards + bakc_rewards_2) // 10 * 96 // 100 + (mayc_rewards // 2 * 96 // 100))
	compounder.claimNftStaking([1], {'from':admin})
	assert matcher.payments(compounder)== 0
	assert math.isclose(compounder.liquid() - pre_c - pool0_rewards, (bakc_rewards + bakc_rewards_2) // 10 * 96 // 100 + (mayc_rewards // 2 * 96 // 100)) + (bakc_rewards + bakc_rewards_2) * 4 // 10 * 96 // 100
	assert matcher.payments(mix_guy)== 0

def test_claiming_no_fee_primary_bayc(matcher, ape, bayc, ape_staking, nft_guy, dog_guy, coin_guy, chain):
	ape.mint(nft_guy, '100000 ether')
	ape.approve(matcher, 2 ** 256 - 1, {'from':nft_guy})
	matcher.batchClaimRewardsFromMatches([], 1, {'from':nft_guy})
	matcher.matchNftsSelf([2], [], {'from':nft_guy})
	chain.sleep(86400)
	chain.mine()
	bayc_rewards = ape_staking.pendingRewards(1, matcher, 2)
	with reverts('!mtch'):
		matcher.batchClaimRewardsFromMatches([2], 1, {'from':coin_guy})
	matcher.batchClaimRewardsFromMatches([2], 0, {'from':nft_guy})
	assert math.isclose(matcher.payments(nft_guy), bayc_rewards)
	chain.sleep(86400)
	chain.mine()
	bayc_rewards_2 = ape_staking.pendingRewards(1, matcher, 2)
	pre = ape.balanceOf(nft_guy)
	matcher.batchClaimRewardsFromMatches([2], 1, {'from':nft_guy})
	assert math.isclose(ape.balanceOf(nft_guy) - pre, bayc_rewards + bayc_rewards_2)

def test_claiming_no_fee_primary_mayc(matcher, ape, mayc, ape_staking, nft_guy, dog_guy, coin_guy, chain):
	matcher.batchClaimRewardsFromMatches([], 1, {'from':nft_guy})
	mayc.mint(nft_guy, 10)
	mayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	matcher.matchNftsSelf([], [12], {'from':nft_guy})
	(self, dogless, ids, pO, dO) = matcher.matches(3)
	assert (dogless & 1, ids, pO, dO, self) == (0, 12, nft_guy, NULL, True)
	chain.sleep(86400)
	chain.mine()
	mayc_rewards = ape_staking.pendingRewards(2, matcher, 12)
	with reverts('!mtch'):
		matcher.batchClaimRewardsFromMatches([3], 1, {'from':coin_guy})
	matcher.batchClaimRewardsFromMatches([3], 0, {'from':nft_guy})
	assert math.isclose(matcher.payments(nft_guy), mayc_rewards)
	chain.sleep(86400)
	chain.mine()
	mayc_rewards_2 = ape_staking.pendingRewards(2, matcher, 12)
	pre = ape.balanceOf(nft_guy)
	matcher.batchClaimRewardsFromMatches([3], 1, {'from':nft_guy})
	assert math.isclose(ape.balanceOf(nft_guy) - pre, mayc_rewards + mayc_rewards_2)

def test_claim_user_in_both_pairs_bayc_nft_side(matcher, smooth, ape, bayc, bakc, ape_staking, nft_guy, chain, compounder, admin):
	bakc.mint(nft_guy, 10)
	bakc.setApprovalForAll(matcher, True, {'from':nft_guy})
	matcher.depositNfts([3], [], [12], {'from':nft_guy})
	(self, dogless, ids, pO, dO) = matcher.matches(4)
	assert (dogless & 1, ids, pO, dO, self) == (1, (12 << 48) +  3, nft_guy, nft_guy, False)
	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, nft_guy, compounder, nft_guy, compounder)
	reward = ape_staking.pendingRewards(1, smooth, 3)
	reward_d = ape_staking.pendingRewards(3, smooth, 12)
	assert reward > 0
	assert reward_d > 0
	matcher.batchClaimRewardsFromMatches([4], 0, {'from':nft_guy})
	assert math.isclose(matcher.payments(nft_guy) - snap[0], (reward // 2 + 5 * reward_d // 10) * 96 // 100)
	assert math.isclose(matcher.payments(compounder) - snap[1], (reward // 2 + reward_d // 10) * 96 // 100 + (4 * reward_d // 10) * 96 // 100)

	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, nft_guy, compounder, nft_guy, compounder)
	reward = ape_staking.pendingRewards(1, smooth, 3)
	reward_d = ape_staking.pendingRewards(3, smooth, 12)
	assert reward > 0
	assert reward_d > 0
	matcher.batchClaimRewardsFromMatches([4], 0, {'from':nft_guy})
	assert math.isclose(matcher.payments(nft_guy) - snap[0], (reward // 2 + 5 * reward_d // 10) * 96 // 100)
	assert math.isclose(matcher.payments(compounder) - snap[1], (reward // 2 + reward_d // 10) * 96 // 100 + (4 * reward_d // 10) * 96 // 100)

	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, nft_guy, compounder, nft_guy, compounder)
	reward = ape_staking.pendingRewards(1, smooth, 3)
	reward_d = ape_staking.pendingRewards(3, smooth, 12)
	assert reward > 0
	assert reward_d > 0
	matcher.batchClaimRewardsFromMatches([4], 0, {'from':nft_guy})
	assert math.isclose(matcher.payments(nft_guy) - snap[0], (reward // 2 + 5 * reward_d // 10) * 96 // 100)
	assert math.isclose(matcher.payments(compounder) - snap[1],  (reward // 2 + reward_d // 10) * 96 // 100 + (4 * reward_d // 10) * 96 // 100)

def test_claim_user_in_both_pairs_mayc_nft_side(matcher, smooth, ape, mayc, bakc, ape_staking, nft_guy, chain, compounder):
	bakc.mint(nft_guy, 10)
	bakc.setApprovalForAll(matcher, True, {'from':nft_guy})
	matcher.depositNfts([], [13], [13], {'from':nft_guy})
	(self, dogless, ids, pO, dO) = matcher.matches(5)
	assert (dogless & 1, ids, pO, dO, self) == (0, (13 << 48) +  13, nft_guy, nft_guy, False)
	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, nft_guy, compounder, nft_guy, compounder)
	reward = ape_staking.pendingRewards(2, smooth, 13)
	reward_d = ape_staking.pendingRewards(3, smooth, 13)
	assert reward > 0
	assert reward_d > 0
	matcher.batchClaimRewardsFromMatches([5], 0, {'from':nft_guy})
	assert math.isclose(matcher.payments(nft_guy) - snap[0], (reward // 2 + 5 * reward_d // 10) * 96 // 100)
	assert math.isclose(matcher.payments(compounder) - snap[1], (reward // 2 + reward_d // 10) * 96 // 100 + (4 * reward_d // 10) * 96 // 100)

	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, nft_guy, compounder, nft_guy, compounder)
	reward = ape_staking.pendingRewards(2, smooth, 13)
	reward_d = ape_staking.pendingRewards(3, smooth, 13)
	assert reward > 0
	assert reward_d > 0
	matcher.batchClaimRewardsFromMatches([5], 0, {'from':nft_guy})
	assert math.isclose(matcher.payments(nft_guy) - snap[0], (reward // 2 + 5 * reward_d // 10) * 96 // 100)
	assert math.isclose(matcher.payments(compounder) - snap[1], (reward // 2 + reward_d // 10) * 96 // 100 + (4 * reward_d // 10) * 96 // 100)

	chain.sleep(86400)
	chain.mine()
	snap = get_payment_snapshot(matcher, nft_guy, compounder, nft_guy, compounder)
	reward = ape_staking.pendingRewards(2, smooth, 13)
	reward_d = ape_staking.pendingRewards(3, smooth, 13)
	assert reward > 0
	assert reward_d > 0
	matcher.batchClaimRewardsFromMatches([5], 0, {'from':nft_guy})
	assert math.isclose(matcher.payments(nft_guy) - snap[0],  (reward // 2 + 5 * reward_d // 10) * 96 // 100)
	assert math.isclose(matcher.payments(compounder) - snap[1], (reward // 2 + reward_d // 10) * 96 // 100 + (4 * reward_d // 10) * 96 // 100)
