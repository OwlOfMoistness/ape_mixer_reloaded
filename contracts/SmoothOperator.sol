pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "../interfaces/ISmoothOperator.sol";
import "../interfaces/IApeStaking.sol";


contract SmoothOperator is Ownable, ISmoothOperator {

	IApeStaking public constant apeStaking = IApeStaking(0x5954aB967Bc958940b7EB73ee84797Dc8a2AFbb9);
	IERC721Enumerable public constant ALPHA = IERC721Enumerable(0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D);
	IERC721Enumerable public constant BETA = IERC721Enumerable(0x60E4d786628Fea6478F785A6d7e704777c86a7c6);
	IERC721Enumerable public constant GAMMA = IERC721Enumerable(0xba30E5F9Bb24caa003E9f2f0497Ad287FDF95623);
	IERC20 public constant APE = IERC20(0x4d224452801ACEd8B2F0aebE155379bb5D594381);

	uint256 constant ALPHA_SHARE = 10094 ether;
	uint256 constant BETA_SHARE = 2042 ether;
	uint256 constant GAMMA_SHARE = 856 ether;

	address public manager;

	constructor(address _manager) {
		manager = _manager;
		ALPHA.setApprovalForAll(_manager, true);
		BETA.setApprovalForAll(_manager, true);
		GAMMA.setApprovalForAll(_manager, true);
		APE.approve(_manager, type(uint256).max);
		APE.approve(address(apeStaking), type(uint256).max);
	}

	modifier onlyManager() {
		require(msg.sender == manager);
		_;
	}

	function swapPrimaryNft(
		address _primary,
		uint256 _in,
		uint256 _out,
		address _receiver,
		uint256 _gammaId) external onlyManager returns(uint256 totalGamma, uint256 totalPrimary) {
		IERC721Enumerable primary = IERC721Enumerable(_primary);
		IApeStaking.SingleNft[] memory tokens = new IApeStaking.SingleNft[](1);
		IApeStaking.PairNftWithdrawWithAmount[] memory nullPair = new IApeStaking.PairNftWithdrawWithAmount[](0);
		IApeStaking.PairNftWithdrawWithAmount[] memory pair = new IApeStaking.PairNftWithdrawWithAmount[](1);

		tokens[0] = IApeStaking.SingleNft(uint32(_out), uint224(primary == ALPHA ? ALPHA_SHARE : BETA_SHARE));
		pair[0] = IApeStaking.PairNftWithdrawWithAmount(uint32(_out), uint32(_gammaId), uint184(GAMMA_SHARE), true);
		// unstake and unbind dog from primary if it exists
		if (_gammaId > 0) {
			apeStaking.withdrawBAKC(
				primary == ALPHA ? pair : nullPair,
				primary == ALPHA ? nullPair : pair);
			totalGamma = APE.balanceOf(address(this));
		}
		// unstake primary
		if (primary == ALPHA)
			apeStaking.withdrawBAYC(tokens, address(this));
		else
			apeStaking.withdrawMAYC(tokens, address(this));
		primary.transferFrom(address(this), _receiver, _out);
		totalPrimary = APE.balanceOf(address(this)) - totalGamma;
		// send rewards of both dog and primary parties
		APE.transfer(manager, totalPrimary + totalGamma);
		tokens[0].tokenId = uint32(_in);
		// stake new primary
		if (primary == ALPHA)
			apeStaking.depositBAYC(tokens);
		else
			apeStaking.depositMAYC(tokens);
		// stake and bind previous dog to new primary if it exists
		if (_gammaId > 0) {
			IApeStaking.PairNftDepositWithAmount[] memory nullPairD = new IApeStaking.PairNftDepositWithAmount[](0);
			IApeStaking.PairNftDepositWithAmount[] memory pairD = new IApeStaking.PairNftDepositWithAmount[](1);
			pairD[0] = IApeStaking.PairNftDepositWithAmount(uint32(_in), uint32(_gammaId), uint184(GAMMA_SHARE));
			apeStaking.depositBAKC(
				primary == ALPHA ? pairD : nullPairD,
				primary == ALPHA ? nullPairD : pairD);
		}
	}

	function swapDoggoNft(
		address _primary,
		uint256 _primaryId,
		uint256 _in,
		uint256 _out,
		address _receiver) external onlyManager returns(uint256 totalGamma) {
		IERC721Enumerable primary = IERC721Enumerable(_primary);
		IApeStaking.SingleNft[] memory tokens = new IApeStaking.SingleNft[](1);
		IApeStaking.PairNftWithdrawWithAmount[] memory nullPair = new IApeStaking.PairNftWithdrawWithAmount[](0);
		IApeStaking.PairNftWithdrawWithAmount[] memory pair = new IApeStaking.PairNftWithdrawWithAmount[](1);

		tokens[0] = IApeStaking.SingleNft(uint32(_out), uint224(primary == ALPHA ? ALPHA_SHARE : BETA_SHARE));
		pair[0] = IApeStaking.PairNftWithdrawWithAmount(uint32(_primaryId), uint32(_out), uint184(GAMMA_SHARE), true);
		// unstake and unbind dog from primary
		apeStaking.withdrawBAKC(
			primary == ALPHA ? pair : nullPair,
			primary == ALPHA ? nullPair : pair);
		totalGamma = APE.balanceOf(address(this));
		GAMMA.transferFrom(address(this), _receiver, _out);
		// stake and bind previous dog to new primary
		IApeStaking.PairNftDepositWithAmount[] memory nullPairD = new IApeStaking.PairNftDepositWithAmount[](0);
		IApeStaking.PairNftDepositWithAmount[] memory pairD = new IApeStaking.PairNftDepositWithAmount[](1);
		pairD[0] = IApeStaking.PairNftDepositWithAmount(uint32(_primaryId), uint32(_in), uint184(GAMMA_SHARE));
		apeStaking.depositBAKC(
			primary == ALPHA ? pairD : nullPairD,
			primary == ALPHA ? nullPairD : pairD);
				totalGamma = APE.balanceOf(address(this)) - totalGamma;
		// send rewards of dog partiy
		APE.transfer(manager,totalGamma);
	}

	function claim(address _primary, uint256 _tokenId, uint256 _gammaId, bool _claimGamma) public onlyManager returns(uint256) {
		IERC721Enumerable primary = IERC721Enumerable(_primary);
		uint256[] memory tokens = new uint256[](1);
		IApeStaking.PairNft[] memory pair = new IApeStaking.PairNft[](1);
		IApeStaking.PairNft[] memory nullPair = new IApeStaking.PairNft[](0);
		tokens[0] = _tokenId;
		pair[0] = IApeStaking.PairNft(uint128(_tokenId), uint128(_gammaId));
		if (_claimGamma) {
			if (_gammaId > 0)
				apeStaking.claimBAKC(
					primary == ALPHA ? pair : nullPair,
					primary == ALPHA ? nullPair : pair, address(this));
		}
		else {
			if (primary == ALPHA)
				apeStaking.claimBAYC(tokens, address(this));
			else
				apeStaking.claimMAYC(tokens, address(this));
		}
		uint256 total = APE.balanceOf(address(this));
		APE.transfer(manager, total);
		return total;
	}

	function commitNFTs(address _primary, uint256 _tokenId, uint256 _gammaId) external onlyManager {
		IERC721Enumerable primary = IERC721Enumerable(_primary);
		IApeStaking.SingleNft[] memory tokens = new IApeStaking.SingleNft[](1);
		tokens[0] = IApeStaking.SingleNft(uint32(_tokenId), uint224(primary == ALPHA ? ALPHA_SHARE : BETA_SHARE));

		IApeStaking.PairNftDepositWithAmount[] memory nullPair = new IApeStaking.PairNftDepositWithAmount[](0);
		IApeStaking.PairNftDepositWithAmount[] memory pair = new IApeStaking.PairNftDepositWithAmount[](1);
		pair[0] = IApeStaking.PairNftDepositWithAmount(uint32(_tokenId), uint32(_gammaId), uint184(GAMMA_SHARE));

		if (primary == ALPHA)
			apeStaking.depositBAYC(tokens);
		else
			apeStaking.depositMAYC(tokens);
		if (_gammaId > 0)
			apeStaking.depositBAKC(
				primary == ALPHA ? pair : nullPair,
				primary == ALPHA ? nullPair : pair);
	}

	function bindDoggoToExistingPrimary(address _primary, uint256 _tokenId, uint256 _gammaId) external onlyManager {
		IERC721Enumerable primary = IERC721Enumerable(_primary);
		IApeStaking.PairNftDepositWithAmount[] memory nullPair = new IApeStaking.PairNftDepositWithAmount[](0);
		IApeStaking.PairNftDepositWithAmount[] memory pair = new IApeStaking.PairNftDepositWithAmount[](1);
		pair[0] = IApeStaking.PairNftDepositWithAmount(uint32(_tokenId), uint32(_gammaId), uint184(GAMMA_SHARE));

		apeStaking.depositBAKC(
			primary == ALPHA ? pair : nullPair,
			primary == ALPHA ? nullPair : pair);
	}

	function unbindDoggoFromExistingPrimary(
		address _primary,
		uint256 _tokenId,
		uint256 _gammaId,
		address _receiver,
		address _tokenOwner) external onlyManager returns(uint256 totalGamma) {
		IERC721Enumerable primary = IERC721Enumerable(_primary);
		IApeStaking.PairNftWithdrawWithAmount[] memory nullPair = new IApeStaking.PairNftWithdrawWithAmount[](0);
		IApeStaking.PairNftWithdrawWithAmount[] memory pair = new IApeStaking.PairNftWithdrawWithAmount[](1);

		pair[0] = IApeStaking.PairNftWithdrawWithAmount(uint32(_tokenId), uint32(_gammaId), uint184(GAMMA_SHARE), true);
		apeStaking.withdrawBAKC(
			primary == ALPHA ? pair : nullPair,
			primary == ALPHA ? nullPair : pair);
		GAMMA.transferFrom(address(this), _receiver, _gammaId);
		APE.transfer(_tokenOwner, GAMMA_SHARE);
		totalGamma = APE.balanceOf(address(this));
		APE.transfer(manager, totalGamma);
	}

	function uncommitNFTs(GreatMatch calldata _match) external onlyManager returns(uint256 totalPrimary, uint256 totalGamma) {
		IERC721Enumerable primary = _match.primary == 1 ? ALPHA : BETA;
		uint256 tokenId = uint256(_match.ids & (2**48 - 1));
		uint256 gammaId = uint256(_match.ids >> 48);
		uint256 primaryShare = primary == ALPHA ? ALPHA_SHARE : BETA_SHARE;
		IApeStaking.SingleNft[] memory tokens = new IApeStaking.SingleNft[](1);
		IApeStaking.PairNftWithdrawWithAmount[] memory nullPair = new IApeStaking.PairNftWithdrawWithAmount[](0);
		IApeStaking.PairNftWithdrawWithAmount[] memory pair = new IApeStaking.PairNftWithdrawWithAmount[](1);

		tokens[0] = IApeStaking.SingleNft(uint32(tokenId), uint224(primaryShare));
		pair[0] = IApeStaking.PairNftWithdrawWithAmount(uint32(tokenId), uint32(gammaId), uint184(GAMMA_SHARE), true);
		if (gammaId > 0) {
			apeStaking.withdrawBAKC(
				primary == ALPHA ? pair : nullPair,
				primary == ALPHA ? nullPair : pair);
			GAMMA.transferFrom(address(this), _match.doggoOwner, gammaId);
			APE.transfer(_match.doggoTokensOwner, GAMMA_SHARE);
			totalGamma = APE.balanceOf(address(this));
		}
		if (primary == ALPHA)
			apeStaking.withdrawBAYC(tokens, address(this));
		else
			apeStaking.withdrawMAYC(tokens, address(this));
		primary.transferFrom(address(this), _match.primaryOwner, tokenId);
		APE.transfer(_match.primaryTokensOwner, primaryShare);
		totalPrimary = APE.balanceOf(address(this)) - totalGamma;
		APE.transfer(manager, totalPrimary + totalGamma);
	}

	// As scary as this look, this function can't steal assets.
	// It cannot access NFT contract outside of designated code above.
	// All contracts that needed approval have received approval in the constructor.
	// Only the staking contract and the manager contract can move assets around.
	// A rogue contract call could not transfer nfts or tokens out of this contract.
	// The existence of this function is purely to claim any rewards from snapshots taken during the time nfts are chilling here.
	// Blame Dingaling for the addition of this 
	function exec(address _target, bytes calldata _data) external payable onlyOwner {
		require(_target != address(ALPHA) &&
				_target != address(BETA) &&
				_target != address(GAMMA) &&
				_target != address(APE), "Cannot call any assets handled by this contract");
		(bool success,) = _target.call{value:msg.value}(_data);
		require(success);
	}
}