pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract ApeCoin is ERC20("Ape", "APE") {

	function mint(address _to, uint256 _amount) external {
		_mint(_to, _amount);
	}
}