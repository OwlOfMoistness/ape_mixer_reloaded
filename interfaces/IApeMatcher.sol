pragma solidity ^0.8.17;

interface IApeMatcher {
	struct GreatMatch {
		uint96	doglessIndex;		// this var will hold primary data in first right most bit. 1 is alpha, 0 is beta
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
		uint256 toMatch;
		uint256 pAvail;
		uint256 dAvail;
		uint256 gammaCount;
		bool gamma;
	}

	function depositApeTokenForUser(uint256 _type, address _user) external;
	function batchClaimRewardsFromMatches(uint256[] calldata _matchIds, bool _claim) external;
	function withdrawApeToken(DepositWithdrawals[][] calldata _deposits) external;
	function batchBreakMatch(uint256[] calldata _matchIds, bool[] calldata _breakAll) external;
	function batchSmartBreakMatch(uint256[] calldata _matchIds, bool[4][] memory _swapSetup) external;
}