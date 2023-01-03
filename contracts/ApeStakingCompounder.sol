pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../interfaces/IApeStaking.sol";
import "../interfaces/IApeMatcher.sol";
import "../interfaces/IAggregatorV3Interface.sol";

contract ApeStakingCompounder is Ownable {
	IAggregatorV3Interface immutable ETH_FEED_USD = IAggregatorV3Interface(0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419);
	IAggregatorV3Interface immutable APE_FEED_USD = IAggregatorV3Interface(0xD10aBbC76679a20055E167BB80A24ac851b37056);
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
	mapping(address => uint256) public userDebt;
	uint256 public totalUserDebt;

	bool public stopBorrow;
	bool public stopCoverFee;

	constructor(address a, address b) {
		APE_STAKING = IApeStaking(a);
		APE = IERC20(b);
		APE.approve(address(APE_STAKING), type(uint256).max);
		keepers[msg.sender] = true;
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


	function borrow(uint256 _amount) external {
		require(msg.sender == address(MATCHER));
		require(!stopBorrow);
		// cannot borrow totalStaked to prevent transferring pending rewards to operator
		require(_amount < liquid());

		debt += _amount;
		APE_STAKING.withdrawApeCoin(_amount, SMOOTH);
	}

	function repay(uint256 _amount) external {
		require(msg.sender == address(MATCHER));
		debt -= _amount;
	}

	function getStakedTotal() public view returns(uint256) {
		uint256 val;
		(val,) = APE_STAKING.addressPosition(address(this));
		return val;
	}

	function liquid() public view returns(uint256) {
		return getStakedTotal() - totalUserDebt;
	}

	function pricePerShare() public view returns(uint256) {
		if (totalSupply == 0)
			return 1e18;
		return ((getStakedTotal() + debt + 
				APE.balanceOf(address(this)) +
				APE_STAKING.pendingRewards(0, address(this), 0)) * 1e18) / totalSupply;
	}

	function pricePerShareBehalf(uint256 _sub) internal view returns(uint256) {
		if (totalSupply == 0)
			return 1e18;
		return ((getStakedTotal() + debt + 
				APE.balanceOf(address(this)) +
				APE_STAKING.pendingRewards(0, address(this), 0) - _sub) * 1e18) / totalSupply;
	}

	function permissionnedDepositFor(uint256 _amount, address _user) public {
		require(msg.sender == address(MATCHER));
		uint256 shares = _amount * 1e18 / pricePerShare();

		balanceOf[_user] += shares;
		totalSupply += shares;
		APE.transferFrom(_user, address(this), _amount);
		compound();
	}

	function depositOnBehalf(uint256 _amount, address _user) external {
		require(msg.sender == address(MATCHER));
		uint256 shares = _amount * 1e18 / pricePerShareBehalf(_amount);

		balanceOf[_user] += shares;
		totalSupply += shares;
		userDebt[_user] += _amount;
		totalUserDebt += _amount;
		compound();
	}

	function deposit(uint256 _amount) external {
		uint256 shares = _amount * 1e18 / pricePerShare();

		balanceOf[msg.sender] += shares;
		totalSupply += shares;
		APE.transferFrom(msg.sender, address(this), _amount);
		compound();
	}

	function withdraw() external {
		withdraw(balanceOf[msg.sender]);
	}

	function withdraw(uint256 _shares) public {
		uint256 value = _shares * pricePerShare() / 1e18;
		uint256 totalValue = balanceOf[msg.sender] * pricePerShare() / 1e18;
		require(totalValue - value >= userDebt[msg.sender]);

		balanceOf[msg.sender] -= _shares;
		totalSupply -= _shares;
		compound();
		APE_STAKING.withdrawApeCoin(value, msg.sender);
	}

	function withdrawExactAmountOnBehalf(uint256 _amount, address _user, address _to) external {
		require(msg.sender == address(MATCHER));
		uint256 sharesToWithdraw = _amount * 1e18 /  pricePerShare();

		balanceOf[_user] -= sharesToWithdraw;
		totalSupply -= sharesToWithdraw;
		userDebt[_user] -= _amount;
		totalUserDebt -= _amount;
		// must be checked as withdrawing the total amount staked results in also transfering the rewards to the recipient
		// which needs to be the vault in our case
		if (_amount == getStakedTotal()) {
			APE_STAKING.withdrawApeCoin(_amount, address(this));
			APE.transfer(_to, _amount);
		}
		else
			APE_STAKING.withdrawApeCoin(_amount, _to);
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

	function calculateApeToRecover(uint256 _gas) internal view returns(uint256) {
		(,int256 apePrice,,,) = APE_FEED_USD.latestRoundData();
		(,int256 ethPrice,,,) = ETH_FEED_USD.latestRoundData();
		uint256 gasPrice = tx.gasprice;
		// Prevent rugging claim, you shouldnt claim if high fees
		if (gasPrice > 80 gwei)
			gasPrice = 80 gwei;
		uint256 usdSpent = _gas * gasPrice * uint256(ethPrice); 

		return usdSpent / uint256(apePrice);
	}

	function batchBreakMatch(uint256[] calldata _matchIds, bool[] calldata _breakAll) external onlyKeepers(msg.sender) {
		uint256 gas = gasleft();
		MATCHER.batchBreakMatch(_matchIds, _breakAll);
		gas = gas - gasleft();
		// if (!stopCoverFee)
		// 	APE.transfer(msg.sender, calculateApeToRecover(gas));
		compound();
	}

	function batchSmartBreakMatch(uint256[] calldata _matchIds, bool[4][] memory _swapSetup) external onlyKeepers(msg.sender) {
		uint256 gas = gasleft();
		MATCHER.batchSmartBreakMatch(_matchIds, _swapSetup);
		gas = gas - gasleft();
		// if (!stopCoverFee)
		// 	APE.transfer(msg.sender, calculateApeToRecover(gas));
		compound();
	}

	function makeMatches() external onlyKeepers(msg.sender) {
		uint256 gas = gasleft();
		uint256[] memory zero = new uint256[](0);
		MATCHER.depositNfts(zero, zero, zero);
		gas = gas - gasleft();
		// if (!stopCoverFee)
		// 	APE.transfer(msg.sender, calculateApeToRecover(gas));
		compound();
	}
}