import pytest
import brownie
import web3
from brownie.test import given, strategy
from brownie import Wei, reverts
import csv

NULL = "0x0000000000000000000000000000000000000000"

def test_deposit_bayc(matcher, bayc, nft_guy):
	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bayc.mint(nft_guy, 10)
	matcher.depositNfts([1,2,3,4,5], [], [], {'from':nft_guy})
	assert bayc.balanceOf(nft_guy) == 5
	assert bayc.balanceOf(matcher) == 5
	for i in range(5):
		assert matcher.assetToUser(bayc, i + 1) == nft_guy

def test_deposit_mayc(matcher, mayc, nft_guy):
	mayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	mayc.mint(nft_guy, 10)
	matcher.depositNfts([], [1,2,3,4,5], [], {'from':nft_guy})
	assert mayc.balanceOf(nft_guy) == 5
	assert mayc.balanceOf(matcher) == 5
	for i in range(5):
		assert matcher.assetToUser(mayc, i + 1) == nft_guy

def test_deposit_bakc(matcher, bakc, nft_guy):
	bakc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bakc.mint(nft_guy, 10)
	matcher.depositNfts([], [], [1,2,3,4,5], {'from':nft_guy})
	assert bakc.balanceOf(nft_guy) == 5
	assert bakc.balanceOf(matcher) == 5
	for i in range(5):
		assert matcher.assetToUser(bakc, i + 1) == nft_guy

def test_withdraw_bayc(matcher, bayc, nft_guy):
	matcher.withdrawNfts([1,2,3,4,5], [], [], {'from':nft_guy})
	assert bayc.balanceOf(nft_guy) == 10
	assert bayc.balanceOf(matcher) == 0
	for i in range(5):
		assert matcher.assetToUser(bayc, i + 1) == NULL

def test_withdraw_mayc(matcher, mayc, nft_guy):
	matcher.withdrawNfts([], [1,2,3,4,5], [], {'from':nft_guy})
	assert mayc.balanceOf(nft_guy) == 10
	assert mayc.balanceOf(matcher) == 0
	for i in range(5):
		assert matcher.assetToUser(mayc, i + 1) == NULL

def test_withdraw_bakc(matcher, bakc, nft_guy):
	matcher.withdrawNfts([], [], [1,2,3,4,5], {'from':nft_guy})
	assert bakc.balanceOf(nft_guy) == 10
	assert bakc.balanceOf(matcher) == 0
	for i in range(5):
		assert matcher.assetToUser(bakc, i + 1) == NULL

def test_multi_deposit(matcher, bayc, mayc, bakc, nft_guy, other_guy):
	matcher.depositNfts([6,7,8,9,10], [6,7,8,9,10], [6,7,8,9,10], {'from':nft_guy})
	assert bayc.balanceOf(nft_guy) == 5
	assert bayc.balanceOf(matcher) == 5
	assert mayc.balanceOf(nft_guy) == 5
	assert mayc.balanceOf(matcher) == 5
	assert bakc.balanceOf(nft_guy) == 5
	assert bakc.balanceOf(matcher) == 5
	for i in range(5):
		assert matcher.assetToUser(bayc, i + 6) == nft_guy
	for i in range(5):
		assert matcher.assetToUser(mayc, i + 6) == nft_guy
	for i in range(5):
		assert matcher.assetToUser(bakc, i + 6) == nft_guy

def test_multi_withdraw(matcher, bayc, mayc, bakc, nft_guy, other_guy):
	matcher.withdrawNfts([6,7,8,9,10], [6,7,8,9,10], [6,7,8,9,10], {'from':nft_guy})
	assert bayc.balanceOf(nft_guy) == 10
	assert bayc.balanceOf(matcher) == 0
	assert mayc.balanceOf(nft_guy) == 10
	assert mayc.balanceOf(matcher) == 0
	assert bakc.balanceOf(nft_guy) == 10
	assert bakc.balanceOf(matcher) == 0
	for i in range(5):
		assert matcher.assetToUser(bayc, i + 6) == NULL
	for i in range(5):
		assert matcher.assetToUser(mayc, i + 6) == NULL
	for i in range(5):
		assert matcher.assetToUser(bakc, i + 6) == NULL


def test_revert_deposit_someone_elses_assets(matcher, bayc, nft_guy, other_guy):
	bayc.setApprovalForAll(matcher, True, {'from':other_guy})
	bayc.mint(other_guy, 10)
	with reverts('!ownr'):
		matcher.depositNfts([11,12], [], [], {'from':nft_guy})
	with reverts('!ownr'):
		matcher.depositNfts([], [1], [], {'from':other_guy})
	with reverts('!ownr'):
		matcher.depositNfts([], [], [1], {'from':other_guy})

def test_revert_withdraw_someone_elses_assets(matcher, bayc, nft_guy, other_guy):
	matcher.depositNfts([1,2,3,4,5], [1,2,3,4,5], [1,2,3,4,5], {'from':nft_guy})
	with reverts('!ownr'):
		matcher.withdrawNfts([1,2,3,4,5], [1,2,3,4,5], [1,2,3,4,5], {'from':other_guy})
	with reverts('!ownr'):
		matcher.withdrawNfts([], [1,2,3,4,5], [1,2,3,4,5], {'from':other_guy})
	with reverts('!ownr'):
		matcher.withdrawNfts([], [], [1,2,3,4,5], {'from':other_guy})

def test_revert_deposit_already_committed(matcher, bayc, ape, ape_staking, nft_guy, other_guy):
	ape.mint(nft_guy, '10094 ether')
	ape.approve(ape_staking, 2 ** 256 - 2, {'from':nft_guy})
	ape_staking.depositBAYC([(6, Wei('10094 ether'))], {'from':nft_guy})
	with reverts('commtd'):
		matcher.depositNfts([6], [], [], {'from':nft_guy})
