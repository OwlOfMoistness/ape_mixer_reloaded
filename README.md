# P2P Single side Apecoin + NFT staking solution

## <ins>What is it?</ins>

Standard NFT staking requires a user to stake both NFT and apecoins to earn more apecoins.

Our solution allows to match users that provide either side of the requirement This enables users to have the choice of `single side staking`.
This removes the need of over exposition of another type of asset. Some users might prefer staying exposed only to NFTs while others prefer only $APE exposition.

Once 2 parties deposit their assets, they get instantly matched and start earning rewards together.

## <ins>How does it work?</ins>

Users can deposit on the contract:
	- BAYC (1 pool)
	- MAYC (1 pool)
	- BAKC (1 pool)
	- $APE in tranches of 10094/2042/856 tokens (3 pools)

This creates 6 pool of assets. When 2 pools (BAYC <> 10094 | MAYC <> 2042 | BAKC <> 856) have assets inside, they are emptied and a match agreement is being created. 
A match is composed of up to 4 people:
	- The primary NFT owner (BAYC/MAYC)
	- The primary apecoin depositor (10094/2042)
	- The Dog owner (optional)
	- The Dog apecoin depositor (856 - optional)

If you are part of 10 agreements, you can claim from those 10 agreements whenever you want.
If your agreement lacks a dog, it may be attached in the future automatically as the pool of those assets gets replenished.
An agreement can't be broken for a specific period of time (7 days for now).
You can exit an agreement before the specific period of time if the asset you are exiting can be replaced by another of similar properties.

## <ins>What's the reward distribution?</ins>

Daily apy pulls will be performed to check the APY of each pool. It is only beneficial for an ape coin holder to stake coins on an nft pool if they earn more than on Pool #0. The meaning share for the ape coin holder should be `Pool #0 APY / Pool #X APY`.
Example: If Pool #0 apy = 100% and Pool #1 APY = 250%, then the minimum split `100 /250 = 40%` for the token holder. As the APYs are closer to each other, the higher the share to the token holder.