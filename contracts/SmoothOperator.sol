// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "../interfaces/ISmoothOperator.sol";
import "../interfaces/IApeStaking.sol";
import "../interfaces/IApeMatcher.sol";
import "./FlashLoanProxy.sol";

contract SmoothOperator is Ownable, ISmoothOperator {

	// IApeStaking public constant apeStaking = IApeStaking(0x5954aB967Bc958940b7EB73ee84797Dc8a2AFbb9);
	// IERC721Enumerable public constant ALPHA = IERC721Enumerable(0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D);
	// IERC721Enumerable public constant BETA = IERC721Enumerable(0x60E4d786628Fea6478F785A6d7e704777c86a7c6);
	// IERC721Enumerable public constant GAMMA = IERC721Enumerable(0xba30E5F9Bb24caa003E9f2f0497Ad287FDF95623);
	// IERC20 public constant APE = IERC20(0x4d224452801ACEd8B2F0aebE155379bb5D594381);

	IApeStaking public APE_STAKING;
	IERC721Enumerable public ALPHA;
	IERC721Enumerable public BETA;
	IERC721Enumerable public GAMMA;
	IERC20 public APE;

	uint256 constant ALPHA_SHARE = 10094 ether;
	uint256 constant BETA_SHARE = 2042 ether;
	uint256 constant GAMMA_SHARE = 856 ether;

	address public manager;

	constructor(address _manager, address a,address b,address c,address d,address e) {
		ALPHA = IERC721Enumerable(a);
		BETA = IERC721Enumerable(b);
		GAMMA = IERC721Enumerable(c);
		APE = IERC20(d);
		APE_STAKING = IApeStaking(e);
		manager = _manager;
		ALPHA.setApprovalForAll(_manager, true);
		BETA.setApprovalForAll(_manager, true);
		GAMMA.setApprovalForAll(_manager, true);
		APE.approve(_manager, type(uint256).max);
		APE.approve(address(APE_STAKING), type(uint256).max);
	}

	modifier onlyManager() {
		require(msg.sender == manager, "Smooth: Can't toucht this");
		_;
	}

	/**
	 * @notice
	 * Function that stakes coins to the vault
	 * @param _vault Contract address of the compound vault
	 * @param _amountToReturn Amount to return
	 */
	function repayDebt(address _vault, uint256 _amountToReturn) external onlyManager {
		APE_STAKING.depositApeCoin(_amountToReturn, _vault);
	}

	/**
	 * @notice
	 * Function that swaps a primary asset from a match
	 * @param _primary Contract address of the primary asset
	 * @param _in New asset ID to be swapped in
	 * @param _out Asset ID to be swapped out
	 * @param _receiver Address receiving the swapped out asset
	 * @param _gammaId Dog ID to uncommit and recommit if it exists
	 */
	function swapPrimaryNft(
		address _primary,
		uint256 _in,
		uint256 _out,
		address _receiver,
		uint256 _gammaId) external onlyManager returns(uint256 totalPrimary, uint256 totalGamma) {
		IERC721Enumerable primary = IERC721Enumerable(_primary);
		IApeStaking.SingleNft[] memory tokens = new IApeStaking.SingleNft[](1);
		IApeStaking.PairNftWithdrawWithAmount[] memory nullPair = new IApeStaking.PairNftWithdrawWithAmount[](0);
		IApeStaking.PairNftWithdrawWithAmount[] memory pair = new IApeStaking.PairNftWithdrawWithAmount[](1);

		tokens[0] = IApeStaking.SingleNft(uint32(_out), uint224(primary == ALPHA ? ALPHA_SHARE : BETA_SHARE));
		pair[0] = IApeStaking.PairNftWithdrawWithAmount(uint32(_out), uint32(_gammaId), uint184(GAMMA_SHARE), true);
		uint256 pre = APE.balanceOf(address(this));
		// unstake and unbind dog from primary if it exists
		if (_gammaId > 0) {
			APE_STAKING.withdrawBAKC(
				primary == ALPHA ? pair : nullPair,
				primary == ALPHA ? nullPair : pair);
			totalGamma = APE.balanceOf(address(this)) - pre - GAMMA_SHARE;
		}
		// unstake primary
		if (primary == ALPHA)
			APE_STAKING.withdrawBAYC(tokens, address(this));
		else
			APE_STAKING.withdrawMAYC(tokens, address(this));
		primary.transferFrom(address(this), _receiver, _out);
		totalPrimary = APE.balanceOf(address(this)) - pre
					- totalGamma - (primary == ALPHA ? ALPHA_SHARE : BETA_SHARE)
					- (_gammaId > 0 ? GAMMA_SHARE : 0);
		tokens[0].tokenId = uint32(_in);
		// stake new primary
		if (primary == ALPHA)
			APE_STAKING.depositBAYC(tokens);
		else
			APE_STAKING.depositMAYC(tokens);
		// stake and bind previous dog to new primary if it exists
		if (_gammaId > 0) {
			IApeStaking.PairNftDepositWithAmount[] memory nullPairD = new IApeStaking.PairNftDepositWithAmount[](0);
			IApeStaking.PairNftDepositWithAmount[] memory pairD = new IApeStaking.PairNftDepositWithAmount[](1);
			pairD[0] = IApeStaking.PairNftDepositWithAmount(uint32(_in), uint32(_gammaId), uint184(GAMMA_SHARE));
			APE_STAKING.depositBAKC(
				primary == ALPHA ? pairD : nullPairD,
				primary == ALPHA ? nullPairD : pairD);
		}
	}

	/**
	 * @notice
	 * Function that swaps a dog asset from a match
	 * @param _primary Contract address of the primary asset
	 * @param _primaryId Primary asset ID to uncommit and recommit
	 * @param _in New dog ID to be swapped in
	 * @param _out DOG ID to be swapped out
	 * @param _receiver Address receiving the swapped out asset
	 */
	function swapDoggoNft(
		address _primary,
		uint256 _primaryId,
		uint256 _in,
		uint256 _out,
		address _receiver) external onlyManager returns(uint256 totalGamma) {
		IERC721Enumerable primary = IERC721Enumerable(_primary);
		IApeStaking.PairNftWithdrawWithAmount[] memory nullPair = new IApeStaking.PairNftWithdrawWithAmount[](0);
		IApeStaking.PairNftWithdrawWithAmount[] memory pair = new IApeStaking.PairNftWithdrawWithAmount[](1);

		pair[0] = IApeStaking.PairNftWithdrawWithAmount(uint32(_primaryId), uint32(_out), uint184(GAMMA_SHARE), true);
		uint256 pre = APE.balanceOf(address(this));
		// unstake and unbind dog from primary
		APE_STAKING.withdrawBAKC(
			primary == ALPHA ? pair : nullPair,
			primary == ALPHA ? nullPair : pair);
		totalGamma = APE.balanceOf(address(this)) - pre - GAMMA_SHARE;
		GAMMA.transferFrom(address(this), _receiver, _out);
		// stake and bind previous dog to new primary
		IApeStaking.PairNftDepositWithAmount[] memory nullPairD = new IApeStaking.PairNftDepositWithAmount[](0);
		IApeStaking.PairNftDepositWithAmount[] memory pairD = new IApeStaking.PairNftDepositWithAmount[](1);
		pairD[0] = IApeStaking.PairNftDepositWithAmount(uint32(_primaryId), uint32(_in), uint184(GAMMA_SHARE));
		APE_STAKING.depositBAKC(
			primary == ALPHA ? pairD : nullPairD,
			primary == ALPHA ? nullPairD : pairD);
	}

	/**
	 * @notice
	 * Function that claims the rewards of a given match
	 * @param _primary Contract address of the primary asset
	 * @param _tokenId Primary asset ID to claim from
	 * @param _gammaId Dog ID to claim from is _claimGamma is true
	 * @param _claimSetup Indicates to claim Dog or primary pr both
	 */
	function claim(address _primary, uint256 _tokenId, uint256 _gammaId, uint256 _claimSetup) public onlyManager returns(uint256 total, uint256 totalGamma) {
		IERC721Enumerable primary = IERC721Enumerable(_primary);
		uint256[] memory tokens = new uint256[](1);
		IApeStaking.PairNft[] memory pair = new IApeStaking.PairNft[](1);
		IApeStaking.PairNft[] memory nullPair = new IApeStaking.PairNft[](0);
		tokens[0] = _tokenId;
		pair[0] = IApeStaking.PairNft(uint128(_tokenId), uint128(_gammaId));
		uint256 pre = APE.balanceOf(address(this));
		if (_claimSetup == 0 || _claimSetup == 2) {
			APE_STAKING.claimBAKC(
				primary == ALPHA ? pair : nullPair,
				primary == ALPHA ? nullPair : pair, address(this));
			totalGamma = APE.balanceOf(address(this)) - pre;
		}
		if (_claimSetup == 1 || _claimSetup == 2){
			if (primary == ALPHA)
				APE_STAKING.claimBAYC(tokens, address(this));
			else
				APE_STAKING.claimMAYC(tokens, address(this));
			total = APE.balanceOf(address(this)) - pre - totalGamma;
		}
	}

	/**
	 * @notice
	 * Function that commits a pair of assets in the staking contract
	 * @param _primary Contract address of the primary asset
	 * @param _tokenId Primary asset ID to commit
	 * @param _gammaId Dog ID to commit if it exists
	 */
	function commitNFTs(address _primary, uint256 _tokenId, uint256 _gammaId) external onlyManager {
		IERC721Enumerable primary = IERC721Enumerable(_primary);
		IApeStaking.SingleNft[] memory tokens = new IApeStaking.SingleNft[](1);
		tokens[0] = IApeStaking.SingleNft(uint32(_tokenId), uint224(primary == ALPHA ? ALPHA_SHARE : BETA_SHARE));

		IApeStaking.PairNftDepositWithAmount[] memory nullPair = new IApeStaking.PairNftDepositWithAmount[](0);
		IApeStaking.PairNftDepositWithAmount[] memory pair = new IApeStaking.PairNftDepositWithAmount[](1);
		pair[0] = IApeStaking.PairNftDepositWithAmount(uint32(_tokenId), uint32(_gammaId), uint184(GAMMA_SHARE));

		if (primary == ALPHA)
			APE_STAKING.depositBAYC(tokens);
		else
			APE_STAKING.depositMAYC(tokens);
		if (_gammaId > 0)
			APE_STAKING.depositBAKC(
				primary == ALPHA ? pair : nullPair,
				primary == ALPHA ? nullPair : pair);
	}

	/**
	 * @notice
	 * Function that binds a dog to a primary asset
	 * @param _primary Contract address of the primary asset
	 * @param _tokenId Primary asset ID
	 * @param _gammaId Dog ID to bind
	 */
	function bindDoggoToExistingPrimary(address _primary, uint256 _tokenId, uint256 _gammaId) external onlyManager {
		IERC721Enumerable primary = IERC721Enumerable(_primary);
		IApeStaking.PairNftDepositWithAmount[] memory nullPair = new IApeStaking.PairNftDepositWithAmount[](0);
		IApeStaking.PairNftDepositWithAmount[] memory pair = new IApeStaking.PairNftDepositWithAmount[](1);
		pair[0] = IApeStaking.PairNftDepositWithAmount(uint32(_tokenId), uint32(_gammaId), uint184(GAMMA_SHARE));

		APE_STAKING.depositBAKC(
			primary == ALPHA ? pair : nullPair,
			primary == ALPHA ? nullPair : pair);
	}

	/**
	 * @notice
	 * Function that unbinds a dog from a primary asset
	 * @param _primary Contract address of the primary asset
	 * @param _tokenId Primary asset ID
	 * @param _gammaId Dog ID to unbind
	 * @param _receiver Owner of dog
	 * @param _caller Address that initiated the execution
	 */
	function unbindDoggoFromExistingPrimary(
		address _primary,
		uint256 _tokenId,
		uint256 _gammaId,
		address _receiver,
		address _caller) external onlyManager returns(uint256 totalGamma, uint256 toReturnToVault) {
		IERC721Enumerable primary = IERC721Enumerable(_primary);
		IApeStaking.PairNftWithdrawWithAmount[] memory nullPair = new IApeStaking.PairNftWithdrawWithAmount[](0);
		IApeStaking.PairNftWithdrawWithAmount[] memory pair = new IApeStaking.PairNftWithdrawWithAmount[](1);

		pair[0] = IApeStaking.PairNftWithdrawWithAmount(uint32(_tokenId), uint32(_gammaId), uint184(GAMMA_SHARE), true);
		uint256 pre = APE.balanceOf(address(this));
		APE_STAKING.withdrawBAKC(
			primary == ALPHA ? pair : nullPair,
			primary == ALPHA ? nullPair : pair);
		totalGamma = APE.balanceOf(address(this)) - pre - GAMMA_SHARE;
		GAMMA.transferFrom(address(this), _receiver == _caller ? _receiver : manager, _gammaId);
		toReturnToVault = GAMMA_SHARE;
	}

	/**
	 * @notice
	 * Function that uncommits all assets from a match
	 * @param _match Contract address of the primary asset
	 * @param _caller Address that initiated the execution
	 */
	function uncommitNFTs(IApeMatcher.GreatMatch calldata _match, address _caller) external onlyManager returns(uint256 totalPrimary, uint256 totalGamma, uint256 toReturn, uint256 toReturnToVault) {
		IERC721Enumerable primary = _match.doglessIndex & 1 == 1 ? ALPHA : BETA;
		uint256 primaryShare = primary == ALPHA ? ALPHA_SHARE : BETA_SHARE;
		IApeStaking.SingleNft[] memory tokens = new IApeStaking.SingleNft[](1);
		IApeStaking.PairNftWithdrawWithAmount[] memory nullPair = new IApeStaking.PairNftWithdrawWithAmount[](0);
		IApeStaking.PairNftWithdrawWithAmount[] memory pair = new IApeStaking.PairNftWithdrawWithAmount[](1);

		tokens[0] = IApeStaking.SingleNft(uint32(_match.ids & (2**48 - 1)), uint224(primaryShare));
		pair[0] = IApeStaking.PairNftWithdrawWithAmount(tokens[0].tokenId, uint32(_match.ids >> 48), uint184(GAMMA_SHARE), true);
		uint256 pre = APE.balanceOf(address(this));
		if (pair[0].bakcTokenId > 0) {
			APE_STAKING.withdrawBAKC(
				primary == ALPHA ? pair : nullPair,
				primary == ALPHA ? nullPair : pair);
			totalGamma = APE.balanceOf(address(this)) - pre - GAMMA_SHARE;
			GAMMA.transferFrom(address(this), _caller == _match.doggoOwner ? _match.doggoOwner : manager, pair[0].bakcTokenId);
			toReturnToVault += GAMMA_SHARE;
		}
		pre = APE.balanceOf(address(this));
		if (primary == ALPHA)
			APE_STAKING.withdrawBAYC(tokens, address(this));
		else
			APE_STAKING.withdrawMAYC(tokens, address(this));
		totalPrimary = APE.balanceOf(address(this)) - pre - primaryShare;
		primary.transferFrom(address(this), _caller == _match.primaryOwner ? _match.primaryOwner : manager, tokens[0].tokenId);
		if (_match.self)
			toReturn += primaryShare;
		else
			toReturnToVault += primaryShare;
	}

	/**
	 * @notice
	 * As scary as this look, this function can't steal assets.
	 * It cannot access NFT contract outside of designated code above.
	 * All contracts that needed approval have received approval in the constructor.
	 * Only the staking contract and the manager contract can move assets around.
	 * A rogue contract call could not transfer nfts or tokens out of this contract.
	 * The existence of this function is purely to claim any rewards from snapshots taken during the time nfts are chilling here.
	 * Blame Dingaling for the addition of this 
	 */
	function exec(address _target, bytes calldata _data) external payable onlyOwner {
		require(_target != address(ALPHA) &&
				_target != address(BETA) &&
				_target != address(GAMMA) &&
				_target != address(APE) &&
				_target != address(APE_STAKING) &&
				_target != address(manager), "Cannot call any assets handled by this contract");
		(bool success,) = _target.call{value:msg.value}(_data);
		require(success);
	}

	address public flashLoanProxy;

	function updateFlashloanProxy(address _proxy) external onlyOwner {
		flashLoanProxy = _proxy;
	}

	function flashloanAsset(address _nft, uint256[] calldata _tokenIds, address _target, bytes calldata _data) external {
		for (uint256 i = 0; i < _tokenIds.length; i++) {
			require(IApeMatcher(manager).assetToUser(_nft, _tokenIds[i]) == msg.sender);

			IERC721Enumerable(_nft).transferFrom(address(this), flashLoanProxy, _tokenIds[i]);
			FlashloanManager(flashLoanProxy).executeFlashLoan(_nft, _tokenIds[i], _target, _data);

			require(IERC721Enumerable(_nft).ownerOf(_tokenIds[i]) == address(this));
			require(IApeMatcher(manager).assetToUser(_nft, _tokenIds[i]) == msg.sender);
			uint256 poolId = _nft == address(ALPHA) ? 1 : (_nft == address(BETA) ? 2 : 3);
			uint256 share = _nft == address(ALPHA) ? ALPHA_SHARE : (_nft == address(BETA) ? BETA_SHARE : GAMMA_SHARE);
			IApeStaking.Position memory pos = APE_STAKING.nftPosition(poolId, _tokenIds[i]);
			require (pos.stakedAmount == share, "incorrect stake");
		}
	}
}