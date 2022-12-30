import pytest
import brownie
import web3
from brownie.test import given, strategy
from brownie import Wei, reverts
import csv

NULL = "0x0000000000000000000000000000000000000000"

def test_revert_operator(matcher, admin):
	assert matcher.smoothOperator() != NULL
	with reverts():
		matcher.setOperator(admin, {'from':admin})

def test_exec_smooth(smooth, admin, bayc, mayc, bakc, ape):
	with reverts('Cannot call any assets handled by this contract'):
		smooth.exec(bayc,'', {'from':admin})
	with reverts('Cannot call any assets handled by this contract'):
		smooth.exec(mayc,'', {'from':admin})
	with reverts('Cannot call any assets handled by this contract'):
		smooth.exec(bakc,'', {'from':admin})
	with reverts('Cannot call any assets handled by this contract'):
		smooth.exec(ape,'', {'from':admin})
	smooth.exec(admin,'', {'from':admin})

def test_ownership(smooth, admin, matcher, dog_guy):
	with reverts('Ownable: caller is not the owner'):
		matcher.transferOwnership(dog_guy, {'from':dog_guy})
	with reverts('Ownable: new owner is the zero address'):
		matcher.transferOwnership(NULL, {'from':admin})
	matcher.transferOwnership(dog_guy, {'from':admin})
	matcher.transferOwnership(admin, {'from':dog_guy})

	with reverts('Ownable: caller is not the owner'):
		smooth.transferOwnership(dog_guy, {'from':dog_guy})
	with reverts('Ownable: new owner is the zero address'):
		smooth.transferOwnership(NULL, {'from':admin})
	smooth.transferOwnership(dog_guy, {'from':admin})
	smooth.transferOwnership(admin, {'from':dog_guy})

def test_smooth_access(smooth, dog_guy):
	with reverts("Smooth: Can't toucht this"):
		smooth.swapPrimaryNft(NULL,0,0,NULL,0, {'from':dog_guy})
	with reverts("Smooth: Can't toucht this"):
		smooth.swapDoggoNft(NULL,0,0,0,NULL, {'from':dog_guy})
	with reverts("Smooth: Can't toucht this"):
		smooth.claim(NULL,0,0,False, {'from':dog_guy})
	with reverts("Smooth: Can't toucht this"):
		smooth.commitNFTs(NULL,0,0, {'from':dog_guy})
	with reverts("Smooth: Can't toucht this"):
		smooth.bindDoggoToExistingPrimary(NULL,0,0, {'from':dog_guy})
	with reverts("Smooth: Can't toucht this"):
		smooth.unbindDoggoFromExistingPrimary(NULL,0,0,NULL,NULL,NULL, {'from':dog_guy})
	with reverts("Smooth: Can't toucht this"):
		smooth.uncommitNFTs((0,0,NULL,NULL,NULL,NULL),NULL, {'from':dog_guy})