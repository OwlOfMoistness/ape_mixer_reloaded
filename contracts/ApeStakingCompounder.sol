// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../interfaces/IApeStaking.sol";
import "../interfaces/IApeMatcher.sol";
import "../interfaces/IAggregatorV3Interface.sol";

contract ApeStakingCompounder is Ownable {
	IAggregatorV3Interface immutable public ETH_FEED_USD = IAggregatorV3Interface(0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419);
	IAggregatorV3Interface immutable public APE_FEED_USD = IAggregatorV3Interface(0xD10aBbC76679a20055E167BB80A24ac851b37056);
	// IApeStaking public immutable APE_STAKING = IApeStaking(0x5954aB967Bc958940b7EB73ee84797Dc8a2AFbb9);
	// IERC20 public immutable APE = IERC20(0x4d224452801ACEd8B2F0aebE155379bb5D594381);

	IApeStaking public APE_STAKING;
	IERC20 public APE;
	IApeMatcher public MATCHER;
	address public SMOOTH;

	mapping(address => bool) keepers;

	uint256 public totalSupply;
	mapping(address => uint256) public balanceOf;
	uint256 public debt;

	bool public stopBorrow;
	bool public stopCoverFee;

	constructor(address a, address b) {
		APE_STAKING = IApeStaking(a);
		APE = IERC20(b);
		APE.approve(address(APE_STAKING), type(uint256).max);
		keepers[msg.sender] = true;
		stopCoverFee = true;
	}

	modifier onlyKeepers(address _keeper) {
		require(keepers[_keeper]);
		_;
	}

	function setKeeper(address _keeper, bool _val) external onlyOwner {
		keepers[_keeper] = _val;
	}

	function borrowSwitch() external onlyOwner {
		stopBorrow = !stopBorrow;
	}

	function coverSwitch() external onlyOwner {
		stopCoverFee = !stopCoverFee;
	}

	function setSmooth(address _smooth) external onlyOwner {
		require(SMOOTH == address(0));
		SMOOTH = _smooth;
	}

	function setMatcher(address _matcher) external onlyOwner {
		require(address(MATCHER) == address(0));
		MATCHER = IApeMatcher(_matcher);
	}

	function getStakedTotal() public view returns(uint256) {
		uint256 val;
		(val,) = APE_STAKING.addressPosition(address(this));
		return val;
	}

	/**  
	 * @notice
	 * View function that allows returns the amount of available borrowable funds int he contract
	 */
	function liquid() public view returns(uint256) {
		return getStakedTotal();
	}

	function pricePerShare() public view returns(uint256) {
		if (totalSupply == 0)
			return 1e18;
		return ((getStakedTotal() + debt + 
				APE.balanceOf(address(this)) +
				APE_STAKING.pendingRewards(0, address(this), 0)) * 1e18) / totalSupply;
	}

	/**  
	 * @notice
	 * External function that allows the matcher contract to borrow funds
	 * @param _amount Amount of tokens to borrow
	 */
	function borrow(uint256 _amount) external {
		require(msg.sender == address(MATCHER));
		uint256 _liquid = liquid();
		if (stopBorrow) _liquid = 0;
		// cannot borrow totalStaked to prevent transferring pending rewards to operator
		require(_amount < _liquid);

		debt += _amount;
		APE_STAKING.withdrawApeCoin(_amount, SMOOTH);
	}

	/**  
	 * @notice
	 * External function that allows the matcher contract to borrow funds and send it to a user for repayment
	 * @param _amount Amount of tokens to borrow
	 * @param _user User receiving the funds
	 */
	function borrowAndWithdrawExactFor(uint256 _amount, address _user) external {
		require(msg.sender == address(MATCHER));
		uint256 _liquid = liquid();
		if (stopBorrow) _liquid = 0;
		require(_amount < _liquid);

		debt += _amount;
		APE_STAKING.withdrawApeCoin(_amount, _user);
	}

	/**  
	 * @notice
	 * Repay debt. Callable by matcher.
	 */
	function repay(uint256 _amount) external {
		require(msg.sender == address(MATCHER));
		debt -= _amount;
	}

	/**  
	 * @notice
	 * Function that allows to deposit funds on behalf of a user
	 * @param _amount Amount to deposit
	 * @param _user User getting the deposit
	 */
	function permissionnedDepositFor(uint256 _amount, address _user) public {
		require(msg.sender == address(MATCHER));
		uint256 shares = _amount * 1e18 / pricePerShare();

		balanceOf[_user] += shares;
		totalSupply += shares;
		APE.transferFrom(msg.sender, address(this), _amount);
		compound();
	}

	/**  
	 * @notice
	 * Function that allows users to deposit funds
	 * @param _amount Amount to deposit
	 */
	function deposit(uint256 _amount) external {
		uint256 shares = _amount * 1e18 / pricePerShare();

		balanceOf[msg.sender] += shares;
		totalSupply += shares;
		APE.transferFrom(msg.sender, address(this), _amount);
		compound();
	}

	/**  
	 * @notice
	 * Function that allows users to withdraw shares
	 */
	function withdraw() external {
		withdraw(balanceOf[msg.sender]);
	}

	/**  
	 * @notice
	 * Function that allows users to withdraw shares
	 * @param _shares Amount to withdraw
	 */
	function withdraw(uint256 _shares) public {
		uint256 value = _shares * pricePerShare() / 1e18;

		balanceOf[msg.sender] -= _shares;
		totalSupply -= _shares;
		compound();
		APE_STAKING.withdrawApeCoin(value, msg.sender);
	}

	function compound() public {
		APE_STAKING.claimSelfApeCoin();
		uint256 bal = APE.balanceOf(address(this));
		if (bal > 0)
			APE_STAKING.depositSelfApeCoin(bal);
	}

	function claimNftStaking(uint256[] calldata _matchIds) external {
		MATCHER.batchClaimRewardsFromMatches(_matchIds, 1);
		compound();
	}


	/**  
	 * @notice
	 * Function that allows refund gas used in APE coins based on price provided by chainlink feeds
	 * @param _gas Gas to be refunded
	 */
	function refundApe(uint256 _gas) internal {
		if (stopCoverFee) return;
		(,int256 apePrice,,,) = APE_FEED_USD.latestRoundData();
		(,int256 ethPrice,,,) = ETH_FEED_USD.latestRoundData();
		uint256 gasPrice = tx.gasprice;
		// Prevent abusing claim, you shouldnt claim if high fees
		if (gasPrice > 80 gwei)
			gasPrice = 80 gwei;
		uint256 usdSpent = _gas * gasPrice * uint256(ethPrice); 
		uint256 toRecover = usdSpent / uint256(apePrice);
		require(toRecover < getStakedTotal());
		APE_STAKING.withdrawApeCoin(toRecover, msg.sender);
	}

	/**  
	 * @notice
	 * Function that allows a keeper to break matches to free some funds
	 * @param _matchIds Match IDs to break
	 * @param _breakAll Boolean array specifying breaking the whole match or just the BAKC
	 */
	function batchBreakMatch(uint256[] calldata _matchIds, bool[] calldata _breakAll) external onlyKeepers(msg.sender) {
		uint256 gas = gasleft();
		MATCHER.batchBreakMatch(_matchIds, _breakAll);
		compound();
		refundApe(gas - gasleft());
	}

	/**  
	 * @notice
	 * Function that allows a keeper to make matches
	 */
	function makeMatches() external onlyKeepers(msg.sender) {
		uint256 gas = gasleft();
		uint256[] memory zero = new uint256[](0);
		MATCHER.depositNfts(zero, zero, zero);
		compound();
		refundApe(gas - gasleft());
	}
}