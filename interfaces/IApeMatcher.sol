pragma solidity ^0.8.17;

interface IApeMatcher {
	struct GreatMatch {
		bool	active;	
		uint8	primary;			// alpha:1/beta:2
		uint96	doglessIndex;
		uint96	ids;				// right most 48 bits => primary | left most 48 bits => doggo
		address	primaryOwner;
		address	primaryTokensOwner;	// owner of ape tokens attributed to primary
		address doggoOwner;
		address	doggoTokensOwner;	// owner of ape tokens attributed to doggo
	}

	struct DepositPosition {
		uint32 count;
		address depositor;
	}

	struct DepositWithdrawals {
		uint128 depositId;
		uint32 amount;
	}

	struct MatchingParams {
		uint256 dogCounter;
		uint256 matchCounter;
		uint256 toMatch;
		uint256 pAvail;
		uint256 dAvail;
		uint256 gammaCount;
		bool gamma;
	}

	function depositApeTokenForUser(uint32[3] calldata _depositAmounts, address _user) external;
	function batchClaimRewardsFromMatches(uint256[] calldata _matchIds, bool _claim) external;
	function withdrawApeToken(DepositWithdrawals[][] calldata _deposits) external;
	function batchBreakMatch(uint256[] calldata _matchIds, bool[] calldata _breakAll) external;
	function batchBreakDogMatch(uint256[] calldata _matchIds) external;
	function batchSmartBreakMatch(uint256[] calldata _matchIds, bool[4][] memory _swapSetup) external;
}