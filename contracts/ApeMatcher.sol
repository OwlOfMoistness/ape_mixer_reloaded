pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./Pausable.sol";
import "../interfaces/IApeMatcher.sol";
import "../interfaces/ISmoothOperator.sol";
import "../interfaces/IApeStaking.sol";

contract ApeMatcher is Pausable, IApeMatcher {

	uint256 constant public MIN_STAKING_PERIOD = 7 days;
	uint256 constant public FEE = 40; // 4%
	uint256 constant public DENOMINATOR = 1000;

	// IApeStaking public immutable APE_STAKING = IApeStaking(0x5954aB967Bc958940b7EB73ee84797Dc8a2AFbb9);
	// IERC721Enumerable public immutable ALPHA = IERC721Enumerable(0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D);
	// IERC721Enumerable public immutable BETA = IERC721Enumerable(0x60E4d786628Fea6478F785A6d7e704777c86a7c6);
	// IERC721Enumerable public immutable GAMMA = IERC721Enumerable(0xba30E5F9Bb24caa003E9f2f0497Ad287FDF95623);
	// IERC20 public immutable APE = IERC20(0x4d224452801ACEd8B2F0aebE155379bb5D594381);

	IApeStaking public APE_STAKING;
	IERC721Enumerable public ALPHA;
	IERC721Enumerable public BETA;
	IERC721Enumerable public GAMMA;
	IERC20 public APE;

	uint256 constant ALPHA_SHARE = 10094 ether; //bayc
	uint256 constant BETA_SHARE = 2042 ether; // mayc
	uint256 constant GAMMA_SHARE = 856 ether; // dog

	uint256 public fee;
	uint256 weights;
	mapping(address => mapping(uint256 => address)) public assetToUser;

	uint256 public matchCounter;
	uint256 public doglessMatchCounter;

	uint256 public alphaSpentCounter;
	uint256 public betaSpentCounter;
	uint256 public gammaSpentCounter;

	uint256 public alphaDepositCounter;
	uint256 public betaDepositCounter;
	uint256 public gammaDepositCounter;

	uint256 public alphaCurrentTotalDeposits;
	uint256 public betaCurrentTotalDeposits;
	uint256 public gammaCurrentTotalDeposits;
	mapping(uint256 => mapping(uint256 => DepositPosition)) public depositPosition;

	mapping(uint256 => GreatMatch) public matches;
	mapping(uint256 => uint256) public doglessMatches;
	mapping(address => uint256) public payments;

	ISmoothOperator public smoothOperator; // add interface to our smooth operator

	constructor(address a,address b,address c,address d,address e) {
		ALPHA = IERC721Enumerable(a);
		BETA = IERC721Enumerable(b);
		GAMMA = IERC721Enumerable(c);
		APE = IERC20(d);
		APE_STAKING = IApeStaking(e);
	}

	modifier onlyOperator() {
		require(msg.sender == address(smoothOperator), "!smooooth");
		_;
	}

	function setOperator(address _operator) external onlyOwner {
		require(address(smoothOperator) == address(0));
		smoothOperator = ISmoothOperator(_operator);
	}

	function updateWeights(uint32[4] calldata _primaryWeights, uint32[4] calldata _dogWeights) external onlyOwner {
		require(_primaryWeights[0] + _primaryWeights[1] + _primaryWeights[2] + _primaryWeights[3] == 1000);
		require(_primaryWeights[2] + _primaryWeights[3] == 0);
		require(_dogWeights[0] + _dogWeights[1] + _dogWeights[2] + _dogWeights[3] == 1000);

		uint256 val;
		for(uint256 i = 0; i < 4 ; i++)
			val |= (uint256(_primaryWeights[i]) << (32 * (7 - i))) + (uint256(_dogWeights[i]) << (32 * (3 - i)));
		weights = val;
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
			_depositNfts(GAMMA, _gammaIds, msg.sender);
		if (_alphaIds.length > 0) {
			_depositNfts(ALPHA, _alphaIds, msg.sender);
			_mixAndMatchAlpha();
		}
		if (_betaIds.length > 0) {
			_depositNfts(BETA, _betaIds, msg.sender);
			_mixAndMatchBeta();
		}
		_bindDoggoToMatchId();
	}

	function depositApeTokenForUser(uint32[3] calldata _depositAmounts, address _user) external override onlyOperator {
		uint256 totalDeposit = 0;
		uint256[3] memory depositValues = [ALPHA_SHARE, BETA_SHARE, GAMMA_SHARE];
		for(uint256 i = 0; i < 3; i++) {
			totalDeposit += depositValues[i] * uint256(_depositAmounts[i]);
			if (_depositAmounts[i] > 0)
				_handleDeposit(depositValues[i], _depositAmounts[i], _user);
			// TODO emit event somehow
		}

		_mixAndMatchAlpha();
		_mixAndMatchBeta();
		_bindDoggoToMatchId();
	}

	function depositApeToken(uint32[3] calldata _depositAmounts) external notPaused {
		uint256 totalDeposit = 0;
		uint256[3] memory depositValues = [ALPHA_SHARE, BETA_SHARE, GAMMA_SHARE];
		for(uint256 i = 0; i < 3; i++) {
			totalDeposit += depositValues[i] * uint256(_depositAmounts[i]);
			if (_depositAmounts[i] > 0)
				_handleDeposit(depositValues[i], _depositAmounts[i], msg.sender);
			// TODO emit event somehow
		}
		if (totalDeposit > 0) {
			APE.transferFrom(msg.sender, address(this), totalDeposit);
			_mixAndMatchAlpha();
			_mixAndMatchBeta();
			_bindDoggoToMatchId();
		}
	}

	function withdrawNfts(
		uint256[] calldata _alphaIds,
		uint256[] calldata _betaIds,
		uint256[] calldata _gammaIds) external {
		if (_gammaIds.length > 0)
			_withdrawNfts(GAMMA, _gammaIds, msg.sender);
		if (_alphaIds.length > 0)
			_withdrawNfts(ALPHA, _alphaIds, msg.sender);
		if (_betaIds.length > 0)
			_withdrawNfts(BETA, _betaIds, msg.sender);
	}

	function withdrawApeToken(
		uint256[] calldata _depositIndexAlpha,
		uint256[] calldata _depositIndexBeta,
		uint256[] calldata _depositIndexGamma) external {
		uint256 amountToReturn = 0;
		for (uint256 i = 0 ; i < _depositIndexAlpha.length; i++) {
			amountToReturn += _verifyAndReturnDepositValue(0, _depositIndexAlpha[i], msg.sender);
		}
		for (uint256 i = 0 ; i < _depositIndexBeta.length; i++) {
			amountToReturn += _verifyAndReturnDepositValue(1, _depositIndexBeta[i], msg.sender);
		}
		for (uint256 i = 0 ; i < _depositIndexGamma.length; i++) {
			amountToReturn += _verifyAndReturnDepositValue(2, _depositIndexGamma[i], msg.sender);
		}
		APE.transfer(msg.sender, amountToReturn);
	}

	function claimTokens() external {
		_claimTokens(msg.sender);
	}

	function batchClaimRewardsFromMatches(uint256[] calldata _matchIds, bool _claim) external {
		uint256 _fee;
		for(uint256 i = 0 ; i < _matchIds.length; i++)
			_fee += _claimRewardsFromMatch(_matchIds[i]);
		if (_fee > 0)
			fee += _fee;
		if (_claim)
			_claimTokens(msg.sender);
	}

	function batchBreakMatch(uint256[] calldata _matchIds, bool[] calldata _breakAll) external {
		uint256 _fee;
		for (uint256 i = 0; i < _matchIds.length; i++) 
			_fee += _breakMatch(_matchIds[i], _breakAll[i]);
		if (_fee > 0)
			fee += _fee;
	}

	function batchBreakDogMatch(uint256[] calldata _matchIds) external {
		uint256 _fee;
		for (uint256 i = 0; i < _matchIds.length; i++)
			_fee += _breakDogMatch(_matchIds[i]);
		if (_fee > 0)
			fee += _fee;
	}

	function batchSmartBreakMatch(uint256[] calldata _matchIds, bool[] calldata _swapDogs) external {
		uint256 _fee;
		for (uint256 i = 0; i < _matchIds.length; i++)
			_fee += _smartBreakMatch(_matchIds[i], _swapDogs[i]);
		if (_fee > 0)
			fee += _fee;
	}

	// INTERNAL

	function _claimTokens(address _user) internal {
		uint256 rewards = payments[_user];
		if (rewards > 0) {
			payments[_user] = 0;
			APE.transfer(_user, rewards);
		}
	}

	function _claimRewardsFromMatch(uint256 _matchId) internal returns(uint256 _fee) {
		GreatMatch memory _match = matches[_matchId];
		require(_match.active, "!active");
		address[4] memory adds = [_match.primaryOwner, _match.primaryTokensOwner, _match.doggoOwner,  _match.doggoTokensOwner];
		require(msg.sender == adds[0] || msg.sender == adds[1] ||
				msg.sender == adds[2] || msg.sender == adds[3], "!match");

		bool claimGamma = msg.sender == adds[2] || msg.sender == adds[3];
		bool claimPrimary = msg.sender == adds[0] || msg.sender == adds[1];
		uint256 ids = _match.ids;
		uint256 total = smoothOperator.claim(
			_match.primary == 1 ? address(ALPHA) : address(BETA),
			ids & 0xffffffffffff,
			ids >> 48,
			claimGamma);
		_fee += _processRewards(total, adds, msg.sender, claimGamma);
		if (claimPrimary && claimGamma) {
			total = smoothOperator.claim(
			_match.primary == 1 ? address(ALPHA) : address(BETA),
			ids & 0xffffffffffff,
			ids >> 48,
			false);
			_fee += _processRewards(total, adds, msg.sender, false);
		}
	}

	function _smartBreakMatch(uint256 _matchId, bool _swapDog) internal returns(uint256 _fee) {
		GreatMatch memory _match = matches[_matchId];
		require(_match.active, "!active");
		address[4] memory adds = [_match.primaryOwner, _match.primaryTokensOwner, _match.doggoOwner,  _match.doggoTokensOwner];
		require(msg.sender == adds[0] || msg.sender == adds[1] ||
				msg.sender == adds[2] || msg.sender == adds[3], "!match");
		
		uint256 index = 0;
		for (; index < 4; index++)
			if (msg.sender == adds[index])
				break;
		if ((msg.sender == adds[0] || msg.sender == adds[1]) &&
			(msg.sender == adds[2] || msg.sender == adds[3]) && _swapDog)
			index += 2;
		uint256 ids = _match.ids;
		address primary = _match.primary == 1 ? address(ALPHA) : address(BETA);
		(uint256 totalPrimary, uint256 totalGamma) = _smartSwap(index, ids, primary, _matchId, msg.sender);
		if (totalPrimary > 0)
			_fee += _processRewards(totalPrimary, adds, msg.sender, false);
		if (totalGamma > 0)
			_fee += _processRewards(totalGamma, adds, msg.sender, true);
	}

	function _smartSwap(
		uint256 _index,
		uint256 _ids,
		address _primary,
		uint256 _matchId,
		address _user) internal returns (uint256 totalPrimary, uint256 totalGamma) {
		// swap primary nft out
		if (_index == 0) {
			require(IERC721Enumerable(_primary).balanceOf(address(this)) > 0, "ApeMatcher: !primary asset");
			uint256 id = IERC721Enumerable(_primary).tokenOfOwnerByIndex(address(this), 0);
			uint256 oldId = _ids & 0xffffffffffff;
			matches[_matchId].ids = uint96(((_ids >> 48) << 48) | id); // swap primary ids
			matches[_matchId].primaryOwner = assetToUser[_primary][id]; // swap primary owner
			delete assetToUser[_primary][oldId];
			IERC721Enumerable(_primary).transferFrom(address(this), address(smoothOperator), id);
			(totalPrimary, totalGamma) = smoothOperator.swapPrimaryNft(_primary, id, oldId, _user, _ids >> 48);
		}
		// swap token depositor, since tokens are fungible, no movement required, simply consume a deposit and return share to initial depositor
		else if (_index == 1) {
			if (_primary == address(ALPHA)) {
				require(alphaCurrentTotalDeposits > 0, "ApeMatcher: !alpha deposits");
				DepositPosition storage pos = depositPosition[ALPHA_SHARE][alphaSpentCounter]; 
				matches[_matchId].primaryTokensOwner = pos.depositor; // swap primary token owner
				if (pos.count == 1) {
					delete depositPosition[ALPHA_SHARE][alphaSpentCounter];
					alphaSpentCounter++;
				}
				else
					pos.count--;
				alphaCurrentTotalDeposits--;
				APE.transfer(_user, ALPHA_SHARE);
				totalPrimary =  smoothOperator.claim(_primary, _ids & 0xffffffffffff, _ids >> 48, false);
			}
			else {
				require(betaCurrentTotalDeposits > 0, "ApeMatcher: !beta deposits");
				DepositPosition storage pos = depositPosition[BETA_SHARE][betaSpentCounter];
				matches[_matchId].primaryTokensOwner = pos.depositor; // swap primary token owner
				if (pos.count == 1) {
					delete depositPosition[BETA_SHARE][betaSpentCounter];
					betaSpentCounter++;
				}
				else
					pos.count--;
				betaCurrentTotalDeposits--;
				APE.transfer(_user, BETA_SHARE);
				totalPrimary =  smoothOperator.claim(_primary, _ids & 0xffffffffffff, _ids >> 48, false);
			}
		}
		// swap doggo out
		else if (_index == 2) {
			require(GAMMA.balanceOf(address(this)) > 0, "ApeMatcher: !dog asset");
			uint256 id = GAMMA.tokenOfOwnerByIndex(address(this), 0);
			uint256 oldId = _ids >> 48;
			matches[_matchId].ids = uint96((_ids & 0xffffffffffff) | (id << 48)); // swap gamma ids
			matches[_matchId].doggoOwner = assetToUser[address(GAMMA)][id]; // swap gamma owner
			delete assetToUser[address(GAMMA)][oldId];
			GAMMA.transferFrom(address(this), address(smoothOperator), id);
			totalGamma = smoothOperator.swapDoggoNft(_primary, _ids & 0xffffffffffff,  id, oldId, _user);
		}
		// swap token depositor, since tokens are fungible, no movement required, simply consume a deposit and return share to initial depositor
		else if (_index == 3) {
			require(gammaCurrentTotalDeposits > 0, "ApeMatcher: !dog deposit");
			DepositPosition storage pos = depositPosition[GAMMA_SHARE][gammaSpentCounter];
			matches[_matchId].doggoTokensOwner = pos.depositor; // swap gamma token owner
			if (pos.count == 1) {
					delete depositPosition[GAMMA_SHARE][gammaSpentCounter];
					gammaSpentCounter++;
				}
				else
					pos.count--;
			gammaCurrentTotalDeposits--;
			APE.transfer(_user, GAMMA_SHARE);
			totalGamma =  smoothOperator.claim(_primary, _ids & 0xffffffffffff, _ids >> 48, true);
		}
	}

	function _breakMatch(uint256 _matchId, bool _breakAll) internal returns(uint256 _fee){
		GreatMatch memory _match = matches[_matchId];
		require(_match.active, "!active");
		address[4] memory adds = [_match.primaryOwner, _match.primaryTokensOwner, _match.doggoOwner,  _match.doggoTokensOwner];
		require(msg.sender == adds[0] || msg.sender == adds[1] ||
				msg.sender == adds[2] || msg.sender == adds[3], "!match");
		require (block.timestamp - _match.start > MIN_STAKING_PERIOD, "Must wait min duration to break clause");
		bool breakGamma = msg.sender == adds[2] || msg.sender == adds[3];
		bool primaryOwner = msg.sender == adds[0] || msg.sender == adds[1];
		_breakAll = primaryOwner ? _breakAll : false;
		if(breakGamma && !_breakAll)
			_fee += _breakDogMatch(_matchId);
		else {
			uint256 tokenId = _match.ids;
			matches[_matchId].active = false;
			// ensures all participants receive back their shares
			(uint256 total, uint256 totalGamma) = smoothOperator.uncommitNFTs(_match, msg.sender);
			if (msg.sender == adds[0])
				delete assetToUser[_match.primary == 1 ? address(ALPHA) : address(BETA)][tokenId & 0xffffffffffff];
			if (msg.sender == adds[2] && tokenId >> 48 > 0)
				delete assetToUser[address(GAMMA)][tokenId >> 48];
			delete matches[_matchId];
			_fee += _processRewards(total, adds, msg.sender, false);
			if (totalGamma > 0)
				_fee += _processRewards(totalGamma, adds, msg.sender, true);
		}
	}

	function _breakDogMatch(uint256 _matchId) internal returns(uint256){
		GreatMatch memory _match = matches[_matchId];
		require(_match.active, "!active");
		address[4] memory adds = [_match.primaryOwner, _match.primaryTokensOwner, _match.doggoOwner,  _match.doggoTokensOwner];
		require(msg.sender == adds[2] || msg.sender == adds[3], "!dog match");

		uint256 totalGamma = _unbindDoggoFromMatchId(_matchId, msg.sender);
		return _processRewards(totalGamma, adds, msg.sender, true);
	}

	function _processRewards(uint256 _total, address[4] memory _adds, address _user, bool _claimGamma) internal returns(uint256 _fee){
		uint256 index = 0;
		for (; index < 4; index++)
			if (_user == _adds[index])
				break;
		uint128[4] memory splits = _smartSplit(uint128(_total), _adds, _claimGamma, weights);
		for (uint256 i = 0 ; i < 4; i++)
			if (splits[i] > 0) {
				// If you own both primary nft and deposit token, no fee charged
				if ((i == 0 || i == 1) && _user == _adds[0] && _user == _adds[1] && !_claimGamma)
					payments[_adds[i]] += splits[i];
				else {
					_fee += splits[i] * FEE / DENOMINATOR;
					payments[_adds[i]] += splits[i] - (splits[i] * FEE / DENOMINATOR);
				}
					
			}
	}

	function _smartSplit(uint128 _total, address[4] memory _adds, bool _claimGamma, uint256 _weight) internal pure returns(uint128[4] memory splits) {
		uint256 i = 0;
		splits = _getWeights(_claimGamma, _weight);
		uint128 sum  = 0;
		for (i = 0 ; i < 4 ; i++)
			sum += splits[i];
		// update splits
		for (i = 0 ; i < 4 ; i++)
			splits[i] =  _total * splits[i] / sum;

		for (i = 0 ; i < 3 ; i++)
			for (uint256 j = i + 1 ; j < 4 ; j++) {
				if (_adds[i] == _adds[j] && splits[j] > 0) {
					splits[i] += splits[j];
					splits[j] = 0;
				}
			}
	}

	function _mixAndMatchAlpha() internal {
		uint256 count = ALPHA.balanceOf(address(this));
		uint256 deposits = alphaCurrentTotalDeposits;
		uint256 countGamma = GAMMA.balanceOf(address(this));
		uint256 depositsGamma = gammaCurrentTotalDeposits;
		uint256 matchCount = _min(count, deposits);
		uint256 gammaCount = _min(countGamma, depositsGamma);
		DepositPosition memory primaryPos = DepositPosition(
				depositPosition[ALPHA_SHARE][alphaSpentCounter].count,
				depositPosition[ALPHA_SHARE][alphaSpentCounter].depositor);
		DepositPosition memory gammaPos = DepositPosition(
				depositPosition[GAMMA_SHARE][gammaSpentCounter].count,
				depositPosition[GAMMA_SHARE][gammaSpentCounter].depositor);

		alphaCurrentTotalDeposits -= matchCount;
		gammaCurrentTotalDeposits -= _min(matchCount, gammaCount);
		for (uint256 i = 0; i < matchCount ; i++) {
			bool gammaMatch = i < gammaCount;
			uint256 gammaId = 0;
			uint256 id = ALPHA.tokenOfOwnerByIndex(address(this), 0);
			if (gammaMatch)
				gammaId = GAMMA.tokenOfOwnerByIndex(address(this), 0);
			else {
				doglessMatches[doglessMatchCounter++] = matchCounter;
			}
			matches[matchCounter++] = GreatMatch(
				true,
				uint8(1),
				uint32(block.timestamp),
				uint96((gammaId << 48) + id),
				assetToUser[address(ALPHA)][id],
				primaryPos.depositor,
				gammaMatch ? assetToUser[address(GAMMA)][gammaId] : address(0),
				gammaMatch ? gammaPos.depositor : address(0)
			);
			primaryPos.count--;
			if (gammaMatch)
				gammaPos.count--;
			if (primaryPos.count == 0) {
				alphaSpentCounter++;
				primaryPos = DepositPosition(
					depositPosition[ALPHA_SHARE][alphaSpentCounter].count,
					depositPosition[ALPHA_SHARE][alphaSpentCounter].depositor);
			}
			if (gammaPos.count == 0 && gammaMatch) {
				gammaSpentCounter++;
				gammaPos = DepositPosition(
					depositPosition[GAMMA_SHARE][gammaSpentCounter].count,
					depositPosition[GAMMA_SHARE][gammaSpentCounter].depositor);
			}
			ALPHA.transferFrom(address(this), address(smoothOperator), id);
			if (gammaMatch)
				GAMMA.transferFrom(address(this), address(smoothOperator), gammaId);
			APE.transfer(address(smoothOperator), ALPHA_SHARE + (gammaMatch ? GAMMA_SHARE : 0));
			smoothOperator.commitNFTs(address(ALPHA), id, gammaId);
		}
		depositPosition[ALPHA_SHARE][alphaSpentCounter].count = primaryPos.count;
		depositPosition[GAMMA_SHARE][gammaSpentCounter].count = gammaPos.count;
	}

	function _mixAndMatchBeta() internal {
		uint256 count = BETA.balanceOf(address(this));
		uint256 deposits = betaCurrentTotalDeposits;
		uint256 countGamma = GAMMA.balanceOf(address(this));
		uint256 depositsGamma = gammaCurrentTotalDeposits;
		uint256 matchCount = _min(count, deposits);
		uint256 gammaCount = _min(countGamma, depositsGamma);
		DepositPosition memory primaryPos = DepositPosition(
				depositPosition[BETA_SHARE][betaSpentCounter].count,
				depositPosition[BETA_SHARE][betaSpentCounter].depositor);
		DepositPosition memory gammaPos = DepositPosition(
				depositPosition[GAMMA_SHARE][gammaSpentCounter].count,
				depositPosition[GAMMA_SHARE][gammaSpentCounter].depositor);

		betaCurrentTotalDeposits -= matchCount;
		gammaCurrentTotalDeposits -= _min(matchCount, gammaCount);
		for (uint256 i = 0; i < matchCount ; i++) {
			bool gammaMatch = i < gammaCount;
			uint256 gammaId = 0;
			uint256 id = BETA.tokenOfOwnerByIndex(address(this), 0);
			if (gammaMatch)
				gammaId = GAMMA.tokenOfOwnerByIndex(address(this), 0);
			else {
				doglessMatches[doglessMatchCounter++] = matchCounter;
			}
			matches[matchCounter++] = GreatMatch(
				true,
				uint8(2),
				uint32(block.timestamp),
				uint96((gammaId << 48) + id),
				assetToUser[address(BETA)][id],
				primaryPos.depositor,
				gammaMatch ? assetToUser[address(GAMMA)][gammaId] : address(0),
				gammaMatch ? gammaPos.depositor: address(0)
			);
			primaryPos.count--;
			if (gammaMatch)
				gammaPos.count--;
			if (primaryPos.count == 0) {
				betaSpentCounter++;
				primaryPos = DepositPosition(
					depositPosition[BETA_SHARE][betaSpentCounter].count,
					depositPosition[BETA_SHARE][betaSpentCounter].depositor);
			}
			if (gammaPos.count == 0 && gammaMatch) {
				gammaSpentCounter++;
				gammaPos = DepositPosition(
					depositPosition[GAMMA_SHARE][gammaSpentCounter].count,
					depositPosition[GAMMA_SHARE][gammaSpentCounter].depositor);
			}
			BETA.transferFrom(address(this), address(smoothOperator), id);
			if (gammaMatch)
				GAMMA.transferFrom(address(this), address(smoothOperator), gammaId);
			APE.transfer(address(smoothOperator), BETA_SHARE + (gammaMatch ? GAMMA_SHARE : 0));
			smoothOperator.commitNFTs(address(BETA), id, gammaId);
		}
		depositPosition[BETA_SHARE][betaSpentCounter].count = primaryPos.count;
		depositPosition[GAMMA_SHARE][gammaSpentCounter].count = gammaPos.count;
	}

	function _bindDoggoToMatchId() internal {
		uint256 depositsGamma = gammaCurrentTotalDeposits;
		uint256 toBind = _min(doglessMatchCounter, _min(GAMMA.balanceOf(address(this)), depositsGamma));
		if (toBind == 0) return;
		uint256 doglessIndex = doglessMatchCounter - 1;
		DepositPosition memory gammaPos = DepositPosition(
				depositPosition[GAMMA_SHARE][gammaSpentCounter].count,
				depositPosition[GAMMA_SHARE][gammaSpentCounter].depositor);

		gammaCurrentTotalDeposits -= toBind;
		for (uint256 i = 0; i < toBind; i++) {
			GreatMatch storage _match = matches[doglessMatches[doglessIndex - i]];
			delete doglessMatches[doglessIndex - i];
			uint256 gammaId = GAMMA.tokenOfOwnerByIndex(address(this), 0);
			_match.ids |= uint96(gammaId << 48);
			_match.doggoOwner = assetToUser[address(GAMMA)][gammaId];
			_match.doggoTokensOwner = gammaPos.depositor;
			GAMMA.transferFrom(address(this), address(smoothOperator), gammaId);
			APE.transfer(address(smoothOperator), GAMMA_SHARE);
			address primary = _match.primary == 1 ? address(ALPHA) : address(BETA);
			smoothOperator.bindDoggoToExistingPrimary(primary, _match.ids & 0xffffffffffff, gammaId);
			gammaPos.count--;
			if (gammaPos.count == 0) {
				gammaSpentCounter++;
				gammaPos = DepositPosition(
					depositPosition[GAMMA_SHARE][gammaSpentCounter].count,
					depositPosition[GAMMA_SHARE][gammaSpentCounter].depositor);
			}
		}
		doglessMatchCounter -= toBind;
		depositPosition[GAMMA_SHARE][gammaSpentCounter].count = gammaPos.count;
	}

	function _unbindDoggoFromMatchId(uint256 _matchId, address _caller) internal returns(uint256 totalGamma) {
		GreatMatch storage _match = matches[_matchId];
		address primary = _match.primary == 1 ? address(ALPHA) : address(BETA);
		address dogOwner = _match.doggoOwner;
		uint256 ids = _match.ids;
		totalGamma = smoothOperator.unbindDoggoFromExistingPrimary(
			primary,
			ids & 0xffffffffffff,
			ids >> 48,
			dogOwner,
			_match.doggoTokensOwner,
			_caller);
		if (dogOwner == _caller)	
			delete assetToUser[address(GAMMA)][ids >> 48];
		_match.doggoOwner = address(0);
		_match.doggoTokensOwner = address(0);
		doglessMatches[doglessMatchCounter++] = _matchId;
		_match.ids = uint96(ids & 0xffffffffffff);
	}

	function _handleDeposit(uint256 _type, uint32 _amount, address _user) internal {
		if (_type == ALPHA_SHARE) {
			depositPosition[ALPHA_SHARE][alphaDepositCounter++] = DepositPosition(_amount, _user);
			alphaCurrentTotalDeposits += _amount;
		}
		else if (_type == BETA_SHARE) {
			depositPosition[BETA_SHARE][betaDepositCounter++] =  DepositPosition(_amount, _user);
			betaCurrentTotalDeposits += _amount;
		}
		else if (_type == GAMMA_SHARE) {
			depositPosition[GAMMA_SHARE][gammaDepositCounter++] =  DepositPosition(_amount, _user);
			gammaCurrentTotalDeposits += _amount;
		}
	}

	function _verifyAndReturnDepositValue(uint256 _type, uint256 _index, address _user) internal returns (uint256){
		uint256 count;
		if (_type == 0) {
			require(alphaDepositCounter > _index, "ApeMatcher: deposit !exist");
			require(depositPosition[ALPHA_SHARE][_index].depositor == _user, "ApeMatcher: Not owner of deposit");
			require(alphaSpentCounter <= _index, "ApeMatcher: deposit consumed"); 

			count = depositPosition[ALPHA_SHARE][_index].count;
			alphaCurrentTotalDeposits -= count;
			depositPosition[ALPHA_SHARE][_index] = depositPosition[ALPHA_SHARE][alphaDepositCounter - 1];
			delete depositPosition[ALPHA_SHARE][alphaDepositCounter-- - 1];
			return ALPHA_SHARE * count;
		}
		else if (_type == 1) {
			require(betaDepositCounter > _index, "ApeMatcher: deposit !exist");
			require(depositPosition[BETA_SHARE][_index].depositor == _user, "ApeMatcher: Not owner of deposit");
			require(betaSpentCounter <= _index, "ApeMatcher: deposit consumed");

			count = depositPosition[BETA_SHARE][_index].count;
			betaCurrentTotalDeposits -= count;
			depositPosition[BETA_SHARE][_index] = depositPosition[BETA_SHARE][betaDepositCounter - 1];
			delete depositPosition[BETA_SHARE][betaDepositCounter-- - 1];
			return BETA_SHARE * count;
		}
		else if (_type == 2) {
			require(gammaDepositCounter > _index, "ApeMatcher: deposit !exist");
			require(depositPosition[GAMMA_SHARE][_index].depositor == _user, "ApeMatcher: Not owner of deposit");
			require(gammaSpentCounter <= _index, "ApeMatcher: deposit consumed");

			count = depositPosition[GAMMA_SHARE][_index].count;
			gammaCurrentTotalDeposits -= count;
			depositPosition[GAMMA_SHARE][_index] = depositPosition[GAMMA_SHARE][gammaDepositCounter - 1];
			delete depositPosition[GAMMA_SHARE][gammaDepositCounter-- - 1];
			return GAMMA_SHARE * count;
		}
		else 
			revert("ApeMatcher: Outside keys");
	}

	function _depositNfts(IERC721Enumerable _nft, uint256[] calldata _tokenIds, address _user) internal {
		uint256 poolId = _nft == ALPHA ? 1 : (_nft == BETA ? 2 : 3);
		for(uint256 i = 0; i < _tokenIds.length; i++) {
			IApeStaking.Position memory pos = APE_STAKING.nftPosition(poolId, _tokenIds[i]);
			require (pos.stakedAmount == 0, "ApeMatcher: NFT already commited");
			require(_nft.ownerOf(_tokenIds[i]) == _user, "ApeMatcher: !owner");
			if (_nft == GAMMA && _tokenIds[i] == 0)
				revert("EmperorTomatoKetchup, you can't use your #0");
			assetToUser[address(_nft)][_tokenIds[i]] = _user;
			_nft.transferFrom(_user, address(this), _tokenIds[i]);
		}
	}

	function _withdrawNfts(IERC721Enumerable _nft, uint256[] calldata _tokenIds, address _user) internal {
			for (uint256 i = 0; i < _tokenIds.length; i++) {
			require(assetToUser[address(_nft)][_tokenIds[i]] == _user, "ApeMatcher: !owner");
			delete assetToUser[address(_nft)][_tokenIds[i]];
			_nft.transferFrom(address(this), _user, _tokenIds[i]);
		}
	}

	function _min(uint256 _a, uint256 _b) internal pure returns (uint256) {
		return _a > _b ? _b : _a;
	}

	function _getWeights(bool _claimGamma, uint256 _weight) internal pure returns(uint128[4] memory _weights) {
		uint256 dogMask = (2 << 128) - 1;
		uint256 _uint32Mask = (2 << 32) - 1;
		if (_claimGamma)
			_weight &= dogMask;
		else
			_weight >>= 128;
		_weights[0] = uint128((_weight >> (32 * 3)) & _uint32Mask);
		_weights[1] = uint128((_weight >> (32 * 2)) & _uint32Mask);
		_weights[2] = uint128((_weight >> (32 * 1)) & _uint32Mask);
		_weights[3] = uint128((_weight >> (32 * 0)) & _uint32Mask);
	}
}