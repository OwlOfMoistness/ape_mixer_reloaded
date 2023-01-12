// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.17;

interface IApeMatcher {
	struct GreatMatch {
		bool	self;				// if primary assets self matched
		uint96	doglessIndex;		// this var will hold primary data in first right most bit. 1 is alpha, 0 is beta
		uint96	ids;				// right most 48 bits => primary | left most 48 bits => doggo
		address	primaryOwner;
		address doggoOwner;
	}

	struct MatchingParams {
		uint256 dogCounter;
		uint256 toMatch;
		uint256 gammaCount;
		bool gamma;
	}

	function depositNfts(
		uint256[] calldata _alphaIds,
		uint256[] calldata _betaIds,
		uint256[] calldata _gammaIds) external;
	function batchClaimRewardsFromMatches(uint256[] calldata _matchIds, uint256 _claim) external;
	function batchBreakMatch(uint256[] calldata _matchIds, bool[] calldata _breakAll) external;
	function batchSmartBreakMatch(uint256[] calldata _matchIds, bool[3][] memory _swapSetup) external;
}