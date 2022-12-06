pragma solidity ^0.8.17;

interface IApeMatcher {
	struct GreatMatch {
		bool	paired;				// gamma
		bool	active;	
		uint32	start;				// time of activation
		uint8	primary;			// alpha:1/beta:2
		uint96	ids;				// right most 48 bits => primary | left most 48 bits => doggo
		address	primaryOwner;
		address	primaryTokensOwner;	// owner of ape tokens attributed to primary
		address doggoOwner;
		address	doggoTokensOwner;	// owner of ape tokens attributed to doggo
	}

	//function matches(uint256) external view returns(GreatMatch memory);
}