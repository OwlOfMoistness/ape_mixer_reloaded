pragma solidity ^0.8.17;

interface IApeMatcher {
	struct GreatMatch {
		bool	active;	
		uint8	primary;			// alpha:1/beta:2
		uint32	start;				// time of activation
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

	function depositApeTokenForUser(uint32[3] calldata _depositAmounts, address _user) external;
}