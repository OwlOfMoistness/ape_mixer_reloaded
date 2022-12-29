pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../interfaces/IApeStaking.sol";
import "../interfaces/IApeMatcher.sol";

contract ApeStakingCompounder is Ownable {
	// IApeStaking public immutable APE_STAKING = IApeStaking(0x5954aB967Bc958940b7EB73ee84797Dc8a2AFbb9);
	// IERC20 public immutable APE = IERC20(0x4d224452801ACEd8B2F0aebE155379bb5D594381);

	IApeStaking public APE_STAKING;
	IERC20 public APE;
	IApeMatcher public MATCHER;
	address public SMOOTH;

	uint256 public totalSupply;
	mapping(address => uint256) public balanceOf;
	uint256 public debt;
	mapping(address => uint256) public userDebt;

	constructor(address a, address b) {
		APE_STAKING = IApeStaking(a);
		APE = IERC20(b);
		APE.approve(address(APE_STAKING), type(uint256).max);
	}

	function setSmooth(address _smooth) external onlyOwner {
		require(SMOOTH == address(0));
		SMOOTH = _smooth;
	}

	function setMatcher(address _matcher) external onlyOwner {
		require(SMOOTH == address(0));
		MATCHER = IApeMatcher(_matcher);
	}


	function borrow(uint256 _amount) external {
		require(msg.sender == address(MATCHER));
		require(_amount <= liquid());

		debt += _amount;
		APE_STAKING.withdrawApeCoin(_amount, SMOOTH);
	}

	function repay(uint256 _amount) external {
		require(msg.sender == address(MATCHER));
		require(_amount <= liquid());

		debt -= _amount;
	}

	function liquid() public view returns(uint256) {
		return APE_STAKING.stakedTotal(address(this));
	}

	function pricePerShare() public view returns(uint256) {
		if (totalSupply == 0)
			return 1e18;
		return (APE_STAKING.stakedTotal(address(this)) + debt + 
				APE.balanceOf(address(this)) +
				APE_STAKING.pendingRewards(0, address(this), 0)) * 1e18 / totalSupply;
	}

	function deposit(uint256 _amount) external {
		uint256 shares = _amount * 1e18 / pricePerShare();

		balanceOf[msg.sender] += shares;
		totalSupply += shares;
		APE.transferFrom(msg.sender, address(this), _amount);
		compound();
	}

	function depositOnBehalf(uint256 _amount, address _user) external {
		require(msg.sender == address(MATCHER));
		uint256 shares = _amount * 1e18 / pricePerShare();
	
		balanceOf[_user] += shares;
		totalSupply += shares;
		userDebt[_user] += _amount;
		APE.transferFrom(msg.sender, address(this), _amount);
		compound();
	}

	function withdraw() external {
		withdraw(balanceOf[msg.sender]);
	}

	function withdraw(uint256 _shares) public {
		uint256 value = _shares * pricePerShare() / 1e18;
		uint256 totalValue = balanceOf[msg.sender] * pricePerShare() / 1e18;
		require(totalValue - value > userDebt[msg.sender]);

		balanceOf[msg.sender] -= _shares;
		totalSupply -= _shares;
		compound();
		APE_STAKING.withdrawApeCoin(value, msg.sender);
	}

	function withdrawExactAmountOnBehalf(uint256 _amount, address _user) external {
		require(msg.sender == address(MATCHER));
		uint256 sharesToWithdraw = _amount * 1e18 /  pricePerShare();

		balanceOf[_user] -= sharesToWithdraw;
		totalSupply -= sharesToWithdraw;
		userDebt[_user] -= _amount;
		compound();
		APE_STAKING.withdrawApeCoin(_amount, msg.sender);

	}

	function compound() public {
		APE_STAKING.claimSelfApeCoin();
		uint256 bal = APE.balanceOf(address(this));
		if (bal > 0)
			APE_STAKING.depositSelfApeCoin(bal);
	}

	function claimNftStaking(uint256[] calldata _matchIds) external {
		MATCHER.batchClaimRewardsFromMatches(_matchIds, true);
		compound();
	}

	function withdrawApeToken(IApeMatcher.DepositWithdrawals[][] calldata _deposits) external {
		MATCHER.withdrawApeToken(_deposits);
		compound();
	}

	function batchBreakMatch(uint256[] calldata _matchIds, bool[] calldata _breakAll) external {
		MATCHER.batchBreakMatch(_matchIds, _breakAll);
		compound();
	}

	function batchBreakDogMatch(uint256[] calldata _matchIds) external {
		MATCHER.batchBreakDogMatch(_matchIds);
		compound();
	}

	function batchSmartBreakMatch(uint256[] calldata _matchIds, bool[4][] memory _swapSetup) external {
		MATCHER.batchSmartBreakMatch(_matchIds, _swapSetup);
		compound();
	}
}