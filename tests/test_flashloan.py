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

def test_single_bayc_match(matcher, ape, bayc, nft_guy, coin_guy, smooth, chain, compounder, flash_redeemer, flash_manager, admin):
	bayc.setApprovalForAll(matcher, True, {'from':nft_guy})
	bayc.mint(nft_guy, 10)
	ape.approve(compounder, 2 ** 256 - 1, {'from':coin_guy})
	ape.mint(coin_guy, '320000 ether')
	compounder.deposit('192872 ether', {'from':coin_guy})
	matcher.depositNfts([10], [], [], {'from':nft_guy})

	payload = flash_redeemer.claimForUser.encode_input(10, nft_guy)
	with reverts('imp'):
		smooth.flashloanAsset(bayc, [10], flash_redeemer, payload, {'from':nft_guy})
	flash_manager.setValidImplementation(flash_redeemer, True, {'from':admin})
	pre = ape.balanceOf(nft_guy)
	smooth.flashloanAsset(bayc, [10], flash_redeemer, payload, {'from':nft_guy})
	assert ape.balanceOf(nft_guy) - pre == '1000 ether'
	assert bayc.ownerOf(10) == smooth