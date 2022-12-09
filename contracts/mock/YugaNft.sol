pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";

contract YugaNft is ERC721Enumerable {

	uint256 counter = 0;

	constructor() ERC721("","") {}

	function mint(address _to, uint256 _amount) external {
		uint256 c = counter;
		for (uint256 i = 0; i < _amount; i++)
			_mint(_to, c + 1 + i);
		counter += _amount;
	}
}