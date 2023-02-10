// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./TokenRedeemer.sol";

contract FLTokenRedeemer {

	IERC20 immutable APE;
	TokenRedeemer immutable REDEEMER;

	constructor(address a, address b) {
		REDEEMER = TokenRedeemer(a);
		APE = IERC20(b);
	}

	function claimForUser(uint256 _tokenId, address _beneficiary) external {
		REDEEMER.claim(_tokenId);
		APE.transfer(_beneficiary, APE.balanceOf(address(this)));
	}
}