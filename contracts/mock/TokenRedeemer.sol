// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";
import "./ApeCoin.sol";

contract TokenRedeemer {

	IERC721Enumerable immutable ALPHA;
	ApeCoin immutable APE;

	mapping(uint256 => bool) claimArr;

	constructor(address a, address b) {
		ALPHA = IERC721Enumerable(a);
		APE = ApeCoin(b);
	}

	function claim(uint256 _tokenId) external {
		require(ALPHA.ownerOf(_tokenId) == msg.sender);
		require(!claimArr[_tokenId]);

		claimArr[_tokenId] = true;
		APE.mint(msg.sender, 1000 ether);
	}
}