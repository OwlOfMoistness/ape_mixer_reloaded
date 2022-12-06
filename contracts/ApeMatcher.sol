pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./Pausable.sol";
import "../interfaces/IApeMatcher.sol";
import "../interfaces/ISmoothOperator.sol";

contract ApeMatcher is Pausable, IApeMatcher {

	uint256 constant public MIN_STAKING_PERIOD = 30 days;
	uint256 constant public FEE = 30; // 3%
	uint256 constant public DENOMINATOR = 1000;

	IERC721Enumerable public constant ALPHA = IERC721Enumerable(0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D);
	IERC721Enumerable public constant BETA = IERC721Enumerable(0x60E4d786628Fea6478F785A6d7e704777c86a7c6);
	IERC721Enumerable public constant GAMMA = IERC721Enumerable(0xba30E5F9Bb24caa003E9f2f0497Ad287FDF95623);
	IERC20 public constant APE = IERC20(0x4d224452801ACEd8B2F0aebE155379bb5D594381);

	uint256 constant ALPHA_SHARE = 10094 ether;
	uint256 constant BETA_SHARE = 2042 ether;
	uint256 constant GAMMA_SHARE = 856 ether;

	uint256 fee;
	mapping(address => mapping(uint256 => address)) public assetToUser;

	uint256 public matchCounter;

	uint256 public alphaSpentCounter;
	uint256 public betaSpentCounter;
	uint256 public gammaSpentCounter;

	uint256 public alphaDepositCounter;
	uint256 public betaDepositCounter;
	uint256 public gammaDepositCounter;

	// TODO consider using same mapping feature for nfts to enable restaking if user configs in such way
	// NOTE how => spentocunter decreases and nft is sent at beginning of line, skipping everyone

	mapping(uint256 => mapping(uint256 => address)) public shareDeposits;
	mapping(uint256 => GreatMatch) public matches;
	mapping(uint256 => uint128[4]) public payments;

	ISmoothOperator public smoothOperator; // add interface to our smooth operator

	function setOperator(address _operator) external onlyOwner {
		require(address(smoothOperator) == address(0));
		smoothOperator = ISmoothOperator(_operator);
	}

	function fetchApe() external onlyOwner {
		uint256 amount = fee;
		fee = 0;
		APE.transfer(owner(), amount);
	}

	function depositNfts(
		uint256[] calldata _alphaIds,
		uint256[] calldata _betaIds,
		uint256[] calldata _gammaIds) external notPaused {
		if (_gammaIds.length > 0)
			_depositNfts(GAMMA, _gammaIds);
		if (_alphaIds.length > 0) {
			_depositNfts(ALPHA, _alphaIds);
			_mixAndMatchAlpha();
		}
		if (_betaIds.length > 0) {
			_depositNfts(BETA, _betaIds);
			_mixAndMatchBeta();
		}
	}

	function withdrawNfts(
		uint256[] calldata _alphaIds,
		uint256[] calldata _betaIds,
		uint256[] calldata _gammaIds) external {
		if (_gammaIds.length > 0)
			_withdrawNfts(GAMMA, _gammaIds);
		if (_alphaIds.length > 0)
			_withdrawNfts(ALPHA, _alphaIds);
		if (_betaIds.length > 0)
			_withdrawNfts(BETA, _betaIds);
	}

	function depositApeToken(uint256[] calldata _depositKeys) external notPaused {
		uint256 totalDeposit = 0;
		uint256[3] memory depositValues = [ALPHA_SHARE, BETA_SHARE, GAMMA_SHARE];
		for(uint256 i = 0; i < _depositKeys.length; i++) {
			totalDeposit += depositValues[_depositKeys[i]];
			_handleDeposit(_depositKeys[i], msg.sender);
			// TODO emit event somehow
		}
		require(APE.transferFrom(msg.sender, address(this), totalDeposit), "ApeMatcher: APE token transfer reverted");

		// TODO mix and match
		_mixAndMatchAlpha();
		_mixAndMatchBeta();
	}

	function withdrawApeToken(uint256[] calldata _depositKeys, uint256[] calldata _depositIndex) external {
		require(_depositKeys.length == _depositIndex.length, "ApeMatcher: !length");

		uint256 amountToReturn = 0;
		for (uint256 i = 0 ; i < _depositIndex.length; i++) {
			amountToReturn += _verifyAndReturnDepositValue(_depositKeys[i], _depositIndex[i], msg.sender);
		}
		APE.transfer(msg.sender, amountToReturn);
	}

	function batchClaimRewards(uint256[] calldata _matchIds) external {
		for(uint256 i = 0 ; i < _matchIds.length; i++)
			claimRewards(_matchIds[i]);
	}

	function claimRewards(uint256 _matchId) public {
		GreatMatch memory _match = matches[_matchId];
		require(_match.active, "!active");
		address[4] memory adds = [_match.primaryOwner, _match.primaryTokensOwner, _match.doggoOwner,  _match.doggoTokensOwner];
		require(msg.sender == adds[0] || msg.sender == adds[1] ||
				msg.sender == adds[2] || msg.sender == adds[3]);

		uint256 ids = _match.ids;
		uint256 total = smoothOperator.claim(_match.primary == 1 ? address(ALPHA) : address(BETA), ids & 0xffffffffffff, ids >> 48);
		_processRewards(_matchId, total, adds, _match.primary == 1);
	}

	// TODO make sure everyone is paid
	function breakMatch(uint256 _matchId) external {
		GreatMatch memory _match = matches[_matchId];
		require(_match.active, "!active");
		address[4] memory adds = [_match.primaryOwner, _match.primaryTokensOwner, _match.doggoOwner,  _match.doggoTokensOwner];
		require(msg.sender == adds[0] || msg.sender == adds[1] ||
				msg.sender == adds[2] || msg.sender == adds[3]);
		require (block.timestamp - _match.start > MIN_STAKING_PERIOD, "Must wait min duration to break clause");
		
		uint256 tokenId = _match.ids;
		matches[_matchId].active = false;
		delete assetToUser[_match.primary == 1 ? address(ALPHA) : address(BETA)][tokenId & 0xffffffffffff];
		if (_match.paired)
			delete assetToUser[address(GAMMA)][tokenId >> 48];
		uint256 total = smoothOperator.uncommitNFTs(_match);
		_processRewards(_matchId, total, adds, _match.primary == 1);
	}


	// NOTE instead of killing match in all scenarios, we could check if missing piece exists currently.
	// NOTE if primary owner wants out, check if other primary nft is deposited
	// NOTE if token owner wants out, check if another token deposits exists
	function smartBreakMatch(uint256 _matchId) external {
		GreatMatch memory _match = matches[_matchId];
		require(_match.active, "!active");
		address[4] memory adds = [_match.primaryOwner, _match.primaryTokensOwner, _match.doggoOwner,  _match.doggoTokensOwner];
		require(msg.sender == adds[0] || msg.sender == adds[1] ||
				msg.sender == adds[2] || msg.sender == adds[3]);
		require (block.timestamp - _match.start > MIN_STAKING_PERIOD, "Must wait min duration to break clause");
		
		uint256 index = 0;
		for (; index < 4; index++)
			if (msg.sender == adds[index])
				break;
		uint256 ids = _match.ids;
		uint256 total = smoothOperator.claim(_match.primary == 1 ? address(ALPHA) : address(BETA), ids & 0xffffffffffff, ids >> 48);
		address primary = _match.primary == 1 ? address(ALPHA) : address(BETA);
		_smartSwap(index, ids, primary, _matchId);
		_processRewards(_matchId, total, adds, _match.primary == 1);
	}

	function _smartSwap(uint256 _index, uint256 _ids, address _primary, uint256 _matchId) internal {
		if (_index == 0) {
			if (IERC721Enumerable(_primary).balanceOf(address(this)) > 0) {
				uint256 id = IERC721Enumerable(_primary).tokenOfOwnerByIndex(address(this), 0);
				uint256 oldId = _ids & 0xffffffffffff;
				matches[_matchId].ids = uint96(((_ids >> 48) << 48) | id); // swap primary ids
				matches[_matchId].primaryOwner = assetToUser[_primary][id]; // swap primary owner
				delete assetToUser[_primary][oldId];
				// TODO update last update time?
				smoothOperator.swapPrimaryNft(_primary, id, oldId, msg.sender, _ids >> 48);
			}
		}
		else if (_index == 1) {
			if (_primary == address(ALPHA)) {
				if (alphaDepositCounter - alphaSpentCounter > 0)
					matches[_matchId].primaryTokensOwner = shareDeposits[ALPHA_SHARE][alphaSpentCounter++]; // swap primary token owner
			}
			else {
				if (betaDepositCounter - betaSpentCounter > 0)
					matches[_matchId].primaryTokensOwner = shareDeposits[BETA_SHARE][betaSpentCounter++]; // swap primary token owner
			}
		}
		else if (_index == 2) {
			if (GAMMA.balanceOf(address(this)) > 0) {
				uint256 id = GAMMA.tokenOfOwnerByIndex(address(this), 0);
				uint256 oldId = _ids >> 48;
				matches[_matchId].ids = uint96((_ids & 0xffffffffffff) | id); // swap gamma ids
				matches[_matchId].primaryOwner = assetToUser[address(GAMMA)][id]; // swap gamma owner
				delete assetToUser[address(GAMMA)][oldId];
				// TODO update last update time?
				smoothOperator.swapDoggoNft(_primary, _ids & 0xffffffffffff,  id, oldId, msg.sender);
			}
		}
		else if (_index == 3) {
			if (gammaDepositCounter - gammaSpentCounter > 0)
				matches[_matchId].primaryTokensOwner = shareDeposits[GAMMA_SHARE][gammaSpentCounter++]; // swap gamma token owner
		}
	}

	function _processRewards(uint256 _matchId, uint256 _total, address[4] memory _adds, bool alpha) internal {
		uint256 index = 0;
		for (; index < 4; index++)
			if (msg.sender == _adds[index])
				break;
		uint128[4] memory splits = _smartSplit(uint128(_total), _adds, alpha);
		_total = splits[index] + payments[_matchId][index];
		payments[_matchId][index] = 0;
		splits[index] = 0;
		for (uint256 i = 0 ; i < 4; i++)
			if (splits[i] > 0)
				payments[_matchId][i] += splits[i];
		fee += _total * FEE / DENOMINATOR;
		APE.transfer(msg.sender, _total - _total * FEE / DENOMINATOR);
	}

	function _smartSplit(uint128 _total, address[4] memory _adds, bool _alpha) internal view returns(uint128[4] memory splits) {
		uint256 i = 0;
		splits = _getWeights(_alpha);
		uint128 sum  = 0;
		// make sum and remove weight if address is null
		for (i = 0 ; i < 4 ; i++)
			sum += _adds[i] != address(0) ? splits[i] : 0;
		// update splits
		for (i = 0 ; i < 4 ; i++)
			splits[i] = _adds[i] != address(0) ? ( _total * splits[i] / sum) : 0;

		// if dog owner or dog token deposit owner is primary owner, bring together (saves gas for sstore and transfers)
		if (_adds[0] == _adds[2]) {
			splits[0] += splits[2];
			splits[2] = 0;
		}
		if (_adds[0] == _adds[3]) {
			splits[0] += splits[3];
			splits[3] = 0;
		}
		// if dog owner or dog token deposit owner is primary token deposit owner, bing together (saves gas for sstore and transfers)
		if (_adds[1] == _adds[2]) {
			splits[1] += splits[2];
			splits[2] = 0;
		}
		if (_adds[1] == _adds[3]) {
			splits[1] += splits[3];
			splits[3] = 0;
		}
	}

	function _mixAndMatchAlpha() internal {
		uint256 count = ALPHA.balanceOf(address(this));
		uint256 deposits = alphaDepositCounter - alphaSpentCounter;
		uint256 countGamma = GAMMA.balanceOf(address(this)); // number of dogs in contract | eg : 2 dogs
		uint256 depositsGamma = gammaDepositCounter - gammaSpentCounter; // number of token deposits in contract | eg : 30 deposits => 30 * 856 tokens
		uint256 matchCount = _min(count, deposits);
		uint256 gammaCount = _min(countGamma, depositsGamma);

		for (uint256 i = 0; i < matchCount ; i++) {
			uint256 gammaId = 0;
			uint256 id = ALPHA.tokenOfOwnerByIndex(address(this), 0);
			bool gammaMatch = i < gammaCount;
			if (gammaMatch)
				gammaId = GAMMA.tokenOfOwnerByIndex(address(this), 0);
			matches[matchCount++] = GreatMatch(
				gammaMatch,
				true,
				uint32(block.timestamp),
				uint8(1),
				uint96(gammaId << 48 + id),
				assetToUser[address(ALPHA)][id], // should we delete asset to user for gas saving?
				shareDeposits[ALPHA_SHARE][alphaSpentCounter++], // should we delete asset to user for gas saving?
				gammaMatch ? assetToUser[address(GAMMA)][gammaId] : address(0), // should we delete asset to user for gas saving?
				gammaMatch ? shareDeposits[GAMMA_SHARE][gammaSpentCounter++] : address(0) // should we delete asset to user for gas saving?
			);
			ALPHA.transferFrom(address(this), address(smoothOperator), id);
			if (gammaMatch)
				GAMMA.transferFrom(address(this), address(smoothOperator), gammaId);
			// TODO check if enough ape or need to unstake (if even a thing)
			APE.transfer(address(smoothOperator), ALPHA_SHARE + (gammaMatch ? GAMMA_SHARE : 0));
			// TODO call smooth operator to take/commit nfts and tokens
			smoothOperator.commitNFTs(address(ALPHA), id, gammaId);
		}
	}

	function _mixAndMatchBeta() internal {
		uint256 count = BETA.balanceOf(address(this));
		uint256 deposits = betaDepositCounter - betaSpentCounter;
		uint256 countGamma = GAMMA.balanceOf(address(this));
		uint256 depositsGamma = gammaDepositCounter - gammaSpentCounter;
		uint256 matchCount = _min(count, deposits);

		for (uint256 i = 0; i < matchCount ; i++) {
			uint256 gammaId = 0;
			uint256 id = BETA.tokenOfOwnerByIndex(address(this), 0);
			bool gammaMatch = i < _min(countGamma, depositsGamma);
			if (gammaMatch)
				gammaId = GAMMA.tokenOfOwnerByIndex(address(this), 0);
			matches[matchCount++] = GreatMatch(
				gammaMatch,
				true,
				uint32(block.timestamp),
				uint8(2),
				uint96(gammaId << 48 + id),
				assetToUser[address(BETA)][id], // should we delete asset to user for gas saving?
				shareDeposits[BETA_SHARE][betaSpentCounter++], // should we delete asset to user for gas saving?
				gammaMatch ? assetToUser[address(GAMMA)][gammaId] : address(0), // should we delete asset to user for gas saving?
				gammaMatch ? shareDeposits[GAMMA_SHARE][gammaSpentCounter++]: address(0) // should we delete asset to user for gas saving?
			);
			BETA.transferFrom(address(this), address(smoothOperator), id);
			if (gammaMatch)
				GAMMA.transferFrom(address(this), address(smoothOperator), gammaId);
			// TODO check if enough ape or need to unstake (if even a thing)
			APE.transfer(address(smoothOperator), BETA_SHARE + (gammaMatch ? GAMMA_SHARE : 0));
			// TODO call smooth operator to take/commit nfts and tokens
			smoothOperator.commitNFTs(address(BETA), id, gammaId);
		}
	}

	function _handleDeposit(uint256 _type, address _user) internal {
		if (_type == 0)
			shareDeposits[ALPHA_SHARE][alphaDepositCounter++] = _user;
		else if (_type == 1)
			shareDeposits[BETA_SHARE][betaDepositCounter++] = _user;
		else if (_type == 2)
			shareDeposits[GAMMA_SHARE][gammaDepositCounter++] = _user;
	}

	function _verifyAndReturnDepositValue(uint256 _type, uint256 _index, address _user) internal returns (uint256){
		if (_type == 0) {
			require(shareDeposits[ALPHA_SHARE][_index] == _user, "ApeMatcher: Not owner of deposit");
			require(alphaSpentCounter <= _index, "ApeMatcher: deposit consumed"); 
			require(alphaDepositCounter > _index, "ApeMatcher: deposit !exist");  

			shareDeposits[ALPHA_SHARE][_index] = shareDeposits[ALPHA_SHARE][alphaDepositCounter - 1];
			delete shareDeposits[ALPHA_SHARE][alphaDepositCounter - 1];
			return ALPHA_SHARE;
		}
		else if (_type == 1) {
			require(shareDeposits[BETA_SHARE][_index] == _user, "ApeMatcher: Not owner of deposit");
			require(betaSpentCounter <= _index, "ApeMatcher: deposit consumed");
			require(betaDepositCounter > _index, "ApeMatcher: deposit !exist");

			shareDeposits[BETA_SHARE][_index] = shareDeposits[BETA_SHARE][betaDepositCounter - 1];
			delete shareDeposits[BETA_SHARE][betaDepositCounter - 1];
			return BETA_SHARE;
		}
		else if (_type == 2) {
			require(shareDeposits[GAMMA_SHARE][_index] == _user, "ApeMatcher: Not owner of deposit");
			require(gammaSpentCounter <= _index, "ApeMatcher: deposit consumed");
			require(gammaDepositCounter > _index, "ApeMatcher: deposit !exist");

			shareDeposits[GAMMA_SHARE][_index] = shareDeposits[GAMMA_SHARE][gammaDepositCounter - 1];
			delete shareDeposits[GAMMA_SHARE][gammaDepositCounter - 1];
			return GAMMA_SHARE;
		}
		else 
			revert("ApeMatcher: Outside keys");
	}

	function _depositNfts(IERC721Enumerable _nft, uint256[] calldata _tokenIds) internal {
		for(uint256 i = 0; i < _tokenIds.length; i++) {
			// TODO check asset is not commited by another address
			assetToUser[address(_nft)][_tokenIds[i]] = msg.sender;
			_nft.transferFrom(msg.sender, address(this), _tokenIds[i]);
		}

		// TODO mix and match
	}

	function _withdrawNfts(IERC721Enumerable _nft, uint256[] calldata _tokenIds) internal {
			for (uint256 i = 0; i < _tokenIds.length; i++) {
			require(assetToUser[address(_nft)][_tokenIds[i]] == msg.sender, "!owner");
			delete assetToUser[address(_nft)][_tokenIds[i]];
			_nft.transferFrom(address(this), msg.sender, _tokenIds[i]);
		}
	}

	function _min(uint256 _a, uint256 _b) internal pure returns (uint256) {
		return _a > _b ? _b : _a;
	}

	function _getWeights(bool _alpha) internal pure returns(uint128[4] memory weights) {
		// TODO check if we fetch price feed from bend dao and have a dynamic weight or do static
		// NOTE we should get alpha/beta/gamma weights when they are live. So ultimately we also need to rebalance them slightly
		// NOTE so that primary owners have a larger incentive to be here, and also only need to truly adjust between nft and erc20
		// NOTE depositors
		weights[0] = _alpha ? 1000 : 300; // primary
		weights[1] = _alpha ? 500 : 150;
		weights[2] = _alpha ? 100 : 30;
		weights[3] = _alpha ? 100 : 30;

	}
}