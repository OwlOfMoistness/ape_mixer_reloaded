import brownie
from brownie import Wei, accounts, ApeMatcher, SmoothOperator, Contract


def main():
	ape_staking = Contract('0x5954aB967Bc958940b7EB73ee84797Dc8a2AFbb9')

	(i_p0, i_p1, i_p2, i_p3) = ape_staking.getPoolsUI()
	pool_arr = [i_p0, i_p1, i_p2, i_p3]
	reward_per_range = []
	apys = []
	for pool in pool_arr:
		issuance = ape_staking.rewardsBy(pool[0], pool[2][0], pool[2][1])
		reward_per_range.append(issuance[0])
		apys.append(issuance[0] * 4 / pool[1] * 100)

	i = 0
	print(f'==Pool APYs==')
	for apy in apys:
		print(f'Pool #{i} apy: {int(apy)} %')
		i += 1

	print('')
	print('')
	i = 1
	print(f'==Pool minimum ideal splits==')
	for apy in apys[1:]:
		if (apy < apys[0]):
			print(f'Pool #{i} is not profitable right now, The token holder would be receiving all the rewards and still lose')
		else:
			coin_share = int(apys[0] * 100 // apy)
			print(f'Pool #{i} split {coin_share}:{100 - coin_share} (token holder : nft holder) for the token holder to consider using this pool.')
		i += 1