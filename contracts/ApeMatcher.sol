pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/extensions/IERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./Pausable.sol";
import "../interfaces/IApeMatcher.sol";
import "../interfaces/ISmoothOperator.sol";
import "../interfaces/IApeStaking.sol";
import "../interfaces/IApeCompounder.sol";

contract ApeMatcher is Pausable, IApeMatcher {

	uint256 constant public FEE = 40; // 4%
	uint256 constant public DENOMINATOR = 1000;

	// IApeStaking public immutable APE_STAKING = IApeStaking(0x5954aB967Bc958940b7EB73ee84797Dc8a2AFbb9);
	// IERC721Enumerable public immutable ALPHA = IERC721Enumerable(0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D);
	// IERC721Enumerable public immutable BETA = IERC721Enumerable(0x60E4d786628Fea6478F785A6d7e704777c86a7c6);
	// IERC721Enumerable public immutable GAMMA = IERC721Enumerable(0xba30E5F9Bb24caa003E9f2f0497Ad287FDF95623);
	// IERC20 public immutable APE = IERC20(0x4d224452801ACEd8B2F0aebE155379bb5D594381);

	IApeStaking immutable APE_STAKING;
	IERC721Enumerable immutable ALPHA;
	IERC721Enumerable immutable BETA;
	IERC721Enumerable immutable GAMMA;
	IERC20 immutable APE;

	uint256 constant ALPHA_SHARE = 10094 ether; //bayc
	uint256 constant BETA_SHARE = 2042 ether; // mayc
	uint256 constant GAMMA_SHARE = 856 ether; // dog

	uint256 public fee;
	uint256 public weights;
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

	ISmoothOperator public smoothOperator;
	IApeCompounder public vault;

	constructor(address a,address b,address c,address d,address e) {
		ALPHA = IERC721Enumerable(a);
		BETA = IERC721Enumerable(b);
		GAMMA = IERC721Enumerable(c);
		APE = IERC20(d);
		APE_STAKING = IApeStaking(e);
	}

	modifier onlyOperator() {
		require(msg.sender == address(smoothOperator), "!sm");
		_;
	}

	/**  
	 * @notice
	 * Set the contract to handle NFTs and Ape coins. Can be called only once. Owner gated
	 * @param _operator contract address of the operator
	 * @param _vault contract address of the vault
	 */
	function init(address _operator, address _vault) external onlyOwner {
		require(address(smoothOperator) == address(0) && address(vault) == address(0));
		smoothOperator = ISmoothOperator(_operator);
		vault = IApeCompounder(_vault);
		APE.approve(_vault, type(uint256).max);
	}

	/**  
	 * @notice
	 * Updates the weights that dictates how rewards are split. Owner gated
	 * @param _primaryWeights Array containing the weights for primary splits
	  * @param _dogWeights Array containing the weights for secondary splits
	 */
	function updateWeights(uint32[4] calldata _primaryWeights, uint32[4] calldata _dogWeights) external onlyOwner {
		require(_primaryWeights[0] + _primaryWeights[1] + _primaryWeights[2] + _primaryWeights[3] == 1000);
		require(_primaryWeights[2] + _primaryWeights[3] == 0);
		require(_dogWeights[0] + _dogWeights[1] + _dogWeights[2] + _dogWeights[3] == 1000);

		uint256 val;
		for (uint256 i = 0; i < 4 ; i++)
			val |= (uint256(_primaryWeights[i]) << (32 * (7 - i))) + (uint256(_dogWeights[i]) << (32 * (3 - i)));
		weights = val;
	}

	/**  
	 * @notice
	 * Allows owner to fetch ape coin fees. Owner gated
	 */
	function fetchApe() external onlyOwner {
		uint256 amount = fee;
		fee = 0;
		APE.transferFrom(address(smoothOperator), owner(), amount);
	}

	/**  
	 * @notice
	 * Allows a user to deposit NFTs into the contract
	 * @param _alphaIds Array of BAYC nfts to deposit
	 * @param _betaIds Array of MAYC nfts to deposit
	 * @param _gammaIds Array of BAKC nfts to deposit
	 */
	function depositNfts(
		uint256[] calldata _alphaIds,
		uint256[] calldata _betaIds,
		uint256[] calldata _gammaIds) external notPaused {
			_depositNfts(GAMMA, _gammaIds, msg.sender);
			_depositNfts(ALPHA, _alphaIds, msg.sender);
			_depositNfts(BETA, _betaIds, msg.sender);
		_mixExec();
	}

	/**  
	 * @notice
	 * Allows a user to deposit NFTs into the contract
	 * @param _alphaIds Array of BAYC nfts to deposit
	 * @param _betaIds Array of MAYC nfts to deposit
	 */
	function matchNftsSelf(
		uint256[] calldata _alphaIds,
		uint256[] calldata _betaIds) external notPaused {
			APE.transferFrom(msg.sender, address(smoothOperator),
				_alphaIds.length * ALPHA_SHARE  + _betaIds.length * BETA_SHARE);
			_matchSelf(ALPHA, _alphaIds, 1, msg.sender);
			_matchSelf(BETA, _betaIds, 0, msg.sender);
	}

	/**  
	 * @notice
	 * Allows the operator to deposit the tokens of a user. Used when a match is broken
	 * @param _type Deposits type
	 * @param _user User to deposit to
	 */
	function depositApeTokenForUser(uint256 _type, address _user) external onlyOperator {
		uint256[3] memory depositValues = [ALPHA_SHARE, BETA_SHARE, GAMMA_SHARE];
		uint256 totalDeposit = depositValues[_type];
		if (_user != address(vault)) {
			_handleDeposit(depositValues[_type], 1, _user);
			APE.transferFrom(msg.sender, address(vault), totalDeposit);
			vault.depositOnBehalf(totalDeposit, _user);
			_mixExec();
		}
		else {
			_handleApeTransfer(_user, totalDeposit, false);
		}
	}

	/**  
	 * @notice
	 * Allows a user to deposit ape coins into the contract
	 * @param _depositAmounts Array of amounts of deposits of each tranche to deposit
	 */
	function depositApeToken(uint32[3] calldata _depositAmounts) external notPaused {
		uint256 totalDeposit = 0;
		uint256[3] memory depositValues = [ALPHA_SHARE, BETA_SHARE, GAMMA_SHARE];
		for (uint256 i = 0; i < 3; i++) {
			totalDeposit += depositValues[i] * uint256(_depositAmounts[i]);
			if (_depositAmounts[i] > 0)
				_handleDeposit(depositValues[i], _depositAmounts[i], msg.sender);
			// TODO emit event somehow
		}
		if (totalDeposit > 0) {
			APE.transferFrom(msg.sender, address(vault), totalDeposit);
			vault.depositOnBehalf(totalDeposit, msg.sender);
			_mixExec();
		}
	}

	/**  
	 * @notice
	 * Allows a user withdraw their NFTs that aren't matched
	 * @param _alphaIds Array of BAYC nfts to withdraw
	 * @param _betaIds Array of MAYC nfts to withdraw
	 * @param _gammaIds Array of BAKC nfts to withdraw
	 */
	function withdrawNfts(
		uint256[] calldata _alphaIds,
		uint256[] calldata _betaIds,
		uint256[] calldata _gammaIds) external {
			_withdrawNfts(GAMMA, _gammaIds, msg.sender);
			_withdrawNfts(ALPHA, _alphaIds, msg.sender);
			_withdrawNfts(BETA, _betaIds, msg.sender);
	}

	/**  
	 * @notice
	 * Allows a user withdraw their ape coin deposits that haven't been consumed
	 * @param _deposits Array of deposit IDs of the NFT tranches
	 */
	function withdrawApeToken(
		DepositWithdrawals[][] calldata _deposits) external {
		uint256 amountToReturn = 0;
		for (uint256 i = 0; i < 3; i++) {
			for (uint256 j = 0; j < _deposits[i].length; j++) {
				if (j < _deposits[i].length - 1)
					require(_deposits[i][j].depositId > _deposits[i][j + 1].depositId);
				uint256 share = i == 0 ? ALPHA_SHARE : (i == 1 ? BETA_SHARE : GAMMA_SHARE);
				uint256 _depositCounter = i == 0 ? alphaDepositCounter : (i == 1 ? betaDepositCounter : gammaDepositCounter);
				uint256 _spentCounter = i == 0 ? alphaSpentCounter : (i == 1 ? betaSpentCounter : gammaSpentCounter);
				amountToReturn += _verifyAndReturnDepositValue(
					share, _depositCounter, _spentCounter, _deposits[i][j].depositId, _deposits[i][j].amount, msg.sender);
			}
		}
		_handleApeTransfer(msg.sender, amountToReturn, false);
	}

	/**  
	 * @notice
	 * Allows a user to claim rewards from an array of matches they are involved with
	 * @param _matchIds Array of match IDs a user is involved with 
	 * @param _claim Boolean to set if the users withdraws rewards now or not
	 */
	function batchClaimRewardsFromMatches(uint256[] calldata _matchIds, uint256 _claim) external {
		uint256 _fee;
		for (uint256 i = 0 ; i < _matchIds.length; i++)
			_fee += _claimRewardsFromMatch(_matchIds[i]);
		_handleFeeAndReturn(_fee, address(0), 0, true);
		if (_claim > 0) {
			uint256 totalApe = _claimTokens(msg.sender);
			if (_claim > 1)
				vault.permissionnedDepositFor(totalApe, msg.sender);
		}
	}

	/**  
	 * @notice
	 * Allows a user to break matches they are involved with to recuperate their asset(s)
	 * @param _matchIds Array of match IDs a user is involved with 
	 * @param _breakAll Array of booleans indicating to break the whole match or just the dog agreement
	 */
	function batchBreakMatch(uint256[] calldata _matchIds, bool[] calldata _breakAll) external {
		uint256 _fee;
		uint256 _doglessMatchCounter = doglessMatchCounter;
		uint256 toReturn;
		for (uint256 i = 0; i < _matchIds.length; i++) {
			(uint256 newFee, uint256 doglessOutcome, uint256 _toReturn) = _breakMatch(_matchIds[i], _breakAll[i], _doglessMatchCounter);
			_doglessMatchCounter = doglessOutcome;
			_fee += newFee;
			toReturn += _toReturn;
		}
		doglessMatchCounter = _doglessMatchCounter;
		_handleFeeAndReturn(_fee, msg.sender, toReturn, true);
	}

	/**  
	 * @notice
	 * Allows a user to swap their asset in a match with another one that currently exists in the contract
	 * @param _matchIds Array of match IDs a user is involved with 
	 * @param _swapSetup Array of boolean indicating what the user wants swap in the match
	 */
	function batchSmartBreakMatch(uint256[] calldata _matchIds, bool[4][] memory _swapSetup) external {
		uint256 _totalFee;
		for (uint256 i = 0; i < _matchIds.length; i++) {
			uint256 realisedFee = _smartBreakMatch(_matchIds[i], _swapSetup[i]);
			_totalFee += realisedFee;
		}
		_handleFeeAndReturn(_totalFee, msg.sender, 0, false);
	}

	// INTERNAL

	/**  
	 * @notice
	 * Internal function that claims tokens for a user
	 * @param _user User to send rewards to
	 */
	function _claimTokens(address _user) internal returns (uint256 rewards) {
		rewards = payments[_user];
		if (rewards > 0) {
			payments[_user] = 0;
			APE.transferFrom(address(smoothOperator) ,_user, rewards);
		}
	}

	/**  
	 * @notice
	 * Interncl function that claims tokens from a match
	 * @param _matchId Match ID to claim from
	 */
	function _claimRewardsFromMatch(uint256 _matchId) internal returns(uint256 _fee) {
		(GreatMatch memory _match, address[4] memory adds) = _checkMatch(_matchId);

		bool claimGamma = msg.sender == adds[2] || msg.sender == adds[3];
		bool claimPrimary = msg.sender == adds[0] || msg.sender == adds[1];
		address primary = _match.doglessIndex & 1 == 1 ? address(ALPHA) : address(BETA);
		uint256 ids = _match.ids;
		(uint256 totalPrimary, uint256 totalGamma) = smoothOperator.claim(primary, ids & 0xffffffffffff, ids >> 48,
			claimGamma && claimPrimary ? 2 : (claimGamma ? 0 : 1));
		_fee += _handleRewards(totalPrimary, totalGamma, adds);	
	}

	/**  
	 * @notice
	 * Internal function that claims tokens from a match
	 * @param _matchId Match ID to claim from
	 * @param _swapSetup Boolean array indicating what the user wants swap in the match
	 */
	function _smartBreakMatch(uint256 _matchId, bool[4] memory _swapSetup) internal returns(uint256 _fee) {
		(GreatMatch memory _match, address[4] memory adds) = _checkMatch(_matchId);
		
		for (uint256 i; i < 4; i++)
			_swapSetup[i] = _swapSetup[i] && msg.sender == adds[i];
		uint256 ids = _match.ids;
		address primary = _match.doglessIndex & 1 == 1 ? address(ALPHA) : address(BETA);
		uint256 totalPrimary;
		uint256 totalGamma;
		(totalPrimary, totalGamma) = _smartSwap(_swapSetup, ids, primary, _matchId, msg.sender);
		_fee += _handleRewards(totalPrimary, totalGamma, adds);	
	}

	/**  
	 * @notice
	 * Internal function that handles swapping an asset of a match with another in the contract
	 * @param _swapSetup Boolean array indicating what the user wants swap in the match
	 * @param _ids Ids of primary asset and dog 
	 * @param _primary Contract address of the primary asset
	 * @param _matchId Match ID to execurte the swap
	 * @param _user User to swap out
	 */
	function _smartSwap(
		bool[4] memory _swapSetup,
		uint256 _ids,
		address _primary,
		uint256 _matchId,
		address _user) internal returns (uint256 totalPrimary, uint256 totalGamma) {
		// swap primary nft out
		if (_swapSetup[0]) {
			require(IERC721Enumerable(_primary).balanceOf(address(this)) > 0, "!prim");
			uint256 id = IERC721Enumerable(_primary).tokenOfOwnerByIndex(address(this), 0);
			uint256 oldId = _ids & 0xffffffffffff;
			matches[_matchId].ids = uint96(((_ids >> 48) << 48) | id); // swap primary ids
			matches[_matchId].primaryOwner = assetToUser[_primary][id]; // swap primary owner
			delete assetToUser[_primary][oldId];
			IERC721Enumerable(_primary).transferFrom(address(this), address(smoothOperator), id);
			(totalPrimary, totalGamma) = smoothOperator.swapPrimaryNft(_primary, id, oldId, _user, _ids >> 48);
		}
		// swap token depositor, since tokens are fungible, no movement required, simply consume a deposit and return share to initial depositor
		if (_swapSetup[1]) {
			DepositPosition storage pos;
			if (_primary == address(ALPHA)) {
				require(alphaCurrentTotalDeposits > 0, "!alpha");
				pos = depositPosition[ALPHA_SHARE][alphaSpentCounter]; 
				matches[_matchId].primaryTokensOwner = pos.depositor; // swap primary token owner
				if (pos.count == 1)
					delete depositPosition[ALPHA_SHARE][alphaSpentCounter++];
				else
					pos.count--;
				alphaCurrentTotalDeposits--;
			}
			else {
				require(betaCurrentTotalDeposits > 0, "!beta");
				pos = depositPosition[BETA_SHARE][betaSpentCounter];
				matches[_matchId].primaryTokensOwner = pos.depositor; // swap primary token owner
				if (pos.count == 1)
					delete depositPosition[BETA_SHARE][betaSpentCounter++];
				else
					pos.count--;
				betaCurrentTotalDeposits--;
			}
			_handleSmartReturn(matches[_matchId].primaryTokensOwner, _primary == address(ALPHA) ? ALPHA_SHARE : BETA_SHARE, _user);
			(totalPrimary,) = smoothOperator.claim(_primary, _ids & 0xffffffffffff, _ids >> 48, 1);
		}
		// swap doggo out
		if (_swapSetup[2]) {
			require(GAMMA.balanceOf(address(this)) > 0, "!dog");
			uint256 id = GAMMA.tokenOfOwnerByIndex(address(this), 0);
			uint256 oldId = _ids >> 48;
			matches[_matchId].ids = uint96((_ids & 0xffffffffffff) | (id << 48)); // swap gamma ids
			matches[_matchId].doggoOwner = assetToUser[address(GAMMA)][id]; // swap gamma owner
			delete assetToUser[address(GAMMA)][oldId];
			GAMMA.transferFrom(address(this), address(smoothOperator), id);
			totalGamma = smoothOperator.swapDoggoNft(_primary, _ids & 0xffffffffffff,  id, oldId, _user);
		}
		// swap token depositor, since tokens are fungible, no movement required, simply consume a deposit and return share to initial depositor
		if (_swapSetup[3]) {
			require(gammaCurrentTotalDeposits > 0, "!dog dep");
			DepositPosition storage pos = depositPosition[GAMMA_SHARE][gammaSpentCounter];
			matches[_matchId].doggoTokensOwner = pos.depositor; // swap gamma token owner
			if (pos.count == 1)
					delete depositPosition[GAMMA_SHARE][gammaSpentCounter++];
			else
				pos.count--;
			gammaCurrentTotalDeposits--;
			_handleSmartReturn(matches[_matchId].doggoTokensOwner, GAMMA_SHARE, _user);
			(,totalGamma) = smoothOperator.claim(_primary, _ids & 0xffffffffffff, _ids >> 48, 0);
		}
	}

	/**  
	 * @notice
	 * Internal function that breaks a match
	 * @param _matchId Match ID to break
	 * @param _breakAll Boolean indicating if we break the whole match or just the dogs
	 */
	function _breakMatch(uint256 _matchId, bool _breakAll, uint256 _doglessMatchCounter) internal returns(uint256 _fee, uint256 doglessOutcome, uint256 toReturn){
		(GreatMatch memory _match, address[4] memory adds) = _checkMatch(_matchId);
		bool breakGamma = msg.sender == adds[2] || msg.sender == adds[3];
		bool primaryOwner = msg.sender == adds[0] || msg.sender == adds[1];
		doglessOutcome = _doglessMatchCounter;

		_breakAll = primaryOwner ? _breakAll : false;
		if(breakGamma && !_breakAll) {
			uint256 realisedFee;
			(realisedFee, toReturn) = _breakDogMatch(_matchId, _doglessMatchCounter, adds);
			_fee += realisedFee;
			doglessOutcome++;
		}
		else {
			uint256 tokenId = _match.ids;
			uint256 totalPrimary;
			uint256 totalGamma;
			(totalPrimary, totalGamma, toReturn) = smoothOperator.uncommitNFTs(_match, msg.sender);
			if (msg.sender == adds[0])
				delete assetToUser[_match.doglessIndex & 1 == 1 ? address(ALPHA) : address(BETA)][tokenId & 0xffffffffffff];
			if (msg.sender == adds[2] && tokenId >> 48 > 0)
				delete assetToUser[address(GAMMA)][tokenId >> 48];
			if (adds[2] == address(0)) {
				doglessOutcome--;
				doglessMatches[_match.doglessIndex >> 1] = doglessMatches[doglessMatchCounter - 1];
				delete doglessMatches[doglessMatchCounter - 1];
			}
			delete matches[_matchId];
			_fee += _handleRewards(totalPrimary, totalGamma, adds);	
		}
	}

	/**  
	 * @notice
	 * Internal function that breaks the dog agreement in a match
	 * @param _matchId Match ID to break
	 */
	function _breakDogMatch(uint256 _matchId, uint256 _doglessMatchCounter, address[4] memory _adds) internal returns(uint256, uint256){
		(uint256 totalGamma, uint256 toReturn) = _unbindDoggoFromMatchId(_matchId, msg.sender, _doglessMatchCounter);
		return (_processRewards(totalGamma, _adds, msg.sender, true), toReturn);
	}

	function _handleRewards(uint256 _totalPrimary, uint256 _totalGamma, address[4] memory _adds) internal returns(uint256 _fee) {
		if (_totalPrimary > 0)
			_fee += _processRewards(_totalPrimary, _adds, msg.sender, false);
		if (_totalGamma > 0)
			_fee += _processRewards(_totalGamma, _adds, msg.sender, true);
	}

	/**  
	 * @notice
	 * Internal function that handles the payment from a match to the users involved
	 * @param _total Amount of tokens to distribute to users
	 * @param _adds Array of users involved
	 * @param _user Initial caller of the execution
	 * @param _claimGamma Boolean indicating if the reward came from a primary of dog claim
	 */
	function _processRewards(uint256 _total, address[4] memory _adds, address _user, bool _claimGamma) internal returns(uint256 _fee){
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

	/**  
	 * @notice
	 * Internal function that handles the payment split of a given reward
	 * @param _total Amount of tokens to distribute to users
	 * @param _adds Array of users involved
	 * @param _claimGamma Boolean indicating if the reward came from a primary of dog claim
	 * @param _weight Value holding the split ratios of primary and dog claims
	 */
	function _smartSplit(uint128 _total, address[4] memory _adds, bool _claimGamma, uint256 _weight) internal pure returns(uint128[4] memory splits) {
		uint256 i = 0;
		splits = _getWeights(_claimGamma, _weight);
		uint128 sum  = splits[0] + splits[1] + splits[2] + splits[3];

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

	function mixCount(IERC721Enumerable _nft, uint256 _gammaCount) internal returns(uint256, uint256, uint256, uint256) {
		uint256 balNft = _nft.balanceOf(address(this));
		uint256 gammaShare = GAMMA_SHARE;
		if (balNft == 0)
			return (0,0,0,0);
		uint256 totalDeposits = _nft == ALPHA ? alphaCurrentTotalDeposits : (_nft == BETA ? betaCurrentTotalDeposits : gammaCurrentTotalDeposits);
		uint256 _doglessCount = doglessMatchCounter;
		uint256 liquid = vault.liquid();
		if (liquid > 0) liquid--;
		if (_nft == GAMMA) {
			if (balNft <= totalDeposits)
				return (_min(_doglessCount, balNft), 0, 0, 0);
			uint256 missing = _min(_doglessCount, balNft) > totalDeposits ? _min(_doglessCount, balNft) - totalDeposits : 0;
			uint256 available = _min(liquid / gammaShare, missing);
			if (available > 0) {
				vault.borrow(available * gammaShare);
				return (totalDeposits + available, available, 0, 0);
			}
			return (_min(_doglessCount, totalDeposits), 0, 0, 0);
		}
		else {
			if (balNft <= totalDeposits)
				return (balNft, _gammaCount, 0, 0);
			uint256 share = _nft == ALPHA ? ALPHA_SHARE : BETA_SHARE;
			uint256 available = _min(liquid / share, balNft - totalDeposits);
			uint256 dogAvailable;
			uint256 dogBalance = GAMMA.balanceOf(address(this));
			if (dogBalance > _gammaCount) {
				dogAvailable = _min((liquid - available * share) / gammaShare, dogBalance - _gammaCount);
			}
			if (available > 0 || dogAvailable > 0) {
				vault.borrow(available * share + dogAvailable * gammaShare);
				return (totalDeposits + available, _gammaCount + dogAvailable, available, dogAvailable);
			}
			return (totalDeposits, _gammaCount, 0, 0);
		}
	}

	function getNewDeposit(uint256 _spentCounter, uint256 _share, uint256 _index, uint256 _totalMatches) internal returns(DepositPosition memory) {
		uint32 count = depositPosition[_share][_spentCounter].count;
		address depositor = depositPosition[_share][_spentCounter].depositor;
		DepositPosition memory pos = DepositPosition(count, depositor);
		uint256 toWithdraw = _min(_totalMatches - _index, count) * _share;
		if (toWithdraw > 0)
			vault.withdrawExactAmountOnBehalf(toWithdraw, depositor, address(smoothOperator));
		return pos;
	}

	function _matchSelf(
		IERC721Enumerable _primary,
		uint256[] calldata tokenIds,
		uint8 _type,
		address _user) internal {
		uint256 _matchCounter = matchCounter;
		uint256 _doglessCounter = doglessMatchCounter;

		for (uint256 i = 0; i < tokenIds.length ; i++) {
			assetToUser[address(_primary)][tokenIds[i]] == _user;
			doglessMatches[_doglessCounter] = _matchCounter;
			matches[_matchCounter++] = GreatMatch(
				uint96((_doglessCounter++ << 1) | _type),
				uint96(tokenIds[i]),
				_user,
				_user,
				address(0),
				address(0)
			);
			_primary.transferFrom(_user, address(smoothOperator), tokenIds[i]);
			smoothOperator.commitNFTs(address(_primary), tokenIds[i], 0);
		}
		doglessMatchCounter = _doglessCounter;
		matchCounter = _matchCounter;
	}

	/**  
	 * @notice
	 * Internal function that handles the pairing of primary assets with tokens if they exist
	 * @param _primary Contract address of the primary asset
	 * @param _primaryShare Amount pf tokens required to stake with primary asset
	 * @param _primarySpentCounter Index of token deposit of primary asset
	 */
	function _mixAndMatch(
		IERC721Enumerable _primary,
		uint256 _primaryShare,
		uint256 _primarySpentCounter, uint8 _type) internal {
		uint256 _gammaSpentCounter = gammaSpentCounter;
		uint256 _matchCounter = matchCounter;
		MatchingParams memory p = MatchingParams(doglessMatchCounter,0,0,0,0, false);
		(p.toMatch, p.gammaCount, p.pAvail, p.dAvail) = mixCount(_primary, _min(GAMMA.balanceOf(address(this)), gammaCurrentTotalDeposits));
		DepositPosition memory primaryPos = getNewDeposit(_primarySpentCounter, _primaryShare, 0, p.toMatch - p.pAvail);
		DepositPosition memory gammaPos = getNewDeposit(_gammaSpentCounter, GAMMA_SHARE, 0, _min(p.toMatch, p.gammaCount - p.dAvail));

		if (_primary == ALPHA)
			alphaCurrentTotalDeposits -= p.toMatch - p.pAvail;
		else
			betaCurrentTotalDeposits -= p.toMatch - p.pAvail;
		gammaCurrentTotalDeposits -= _min(p.toMatch, p.gammaCount - p.dAvail);
		for (uint256 i = 0; i < p.toMatch ; i++) {
			uint256 gammaId = 0;
			uint256 id = _primary.tokenOfOwnerByIndex(address(this), 0);
			p.gamma = i < p.gammaCount;
			if (p.gamma)
				gammaId = GAMMA.tokenOfOwnerByIndex(address(this), 0);
			else
				doglessMatches[p.dogCounter++] = _matchCounter;
			matches[_matchCounter++] = GreatMatch(
				p.gamma ? _type : uint96(((p.dogCounter - 1) << 1) | _type),
				uint96((gammaId << 48) + id),
				assetToUser[address(_primary)][id],
				p.pAvail > i ? address(vault) : primaryPos.depositor,
				p.gamma ? assetToUser[address(GAMMA)][gammaId] : address(0),
				p.gamma ? (p.dAvail > i ? address(vault) : gammaPos.depositor) : address(0)
			);
			if (p.pAvail <= i)
				primaryPos.count--;
			if (p.gamma && p.dAvail <= i)
				gammaPos.count--;
			if (primaryPos.count == 0 && p.pAvail <= i) {
				delete depositPosition[_primaryShare][_primarySpentCounter++];
				primaryPos = getNewDeposit(_primarySpentCounter, _primaryShare, i + 1, p.toMatch);
			}
			if (gammaPos.count == 0 && p.gamma && p.pAvail <= i) {
				delete depositPosition[GAMMA_SHARE][_gammaSpentCounter++];
				gammaPos = getNewDeposit(_gammaSpentCounter, GAMMA_SHARE, i + 1, _min(p.toMatch, p.gammaCount));
			}
			_primary.transferFrom(address(this), address(smoothOperator), id);
			if (p.gamma)
				GAMMA.transferFrom(address(this), address(smoothOperator), gammaId);
			smoothOperator.commitNFTs(address(_primary), id, gammaId);
		}
		if (_primary == ALPHA)
			alphaSpentCounter = _primarySpentCounter;
		else
			betaSpentCounter = _primarySpentCounter;
		gammaSpentCounter = _gammaSpentCounter;
		depositPosition[_primaryShare][_primarySpentCounter].count = primaryPos.count;
		depositPosition[GAMMA_SHARE][_gammaSpentCounter].count = gammaPos.count;
		doglessMatchCounter = p.dogCounter;
		matchCounter = _matchCounter;
	}

	/**
	 * @notice
	 * Internal function that handles the pairing of DOG assets with tokens if they exist to an existing dogless match
	 */
	function _bindDoggoToMatchId() internal {
		(uint256 toBind, uint256 dAvail,,) = mixCount(GAMMA, 0);
		if (toBind == 0) return;
		uint256 _gammaSpentCounter = gammaSpentCounter;
		uint256 doglessIndex = doglessMatchCounter - 1;
		uint256 gammaShare = GAMMA_SHARE;
		DepositPosition memory gammaPos = getNewDeposit(_gammaSpentCounter, gammaShare, 0, toBind - dAvail);

		gammaCurrentTotalDeposits -= toBind - dAvail;
		for (uint256 i = 0; i < toBind; i++) {
			GreatMatch storage _match = matches[doglessMatches[doglessIndex - i]];
			uint256 gammaId = GAMMA.tokenOfOwnerByIndex(address(this), 0);
			address primary = _match.doglessIndex & 1 == 1 ? address(ALPHA) : address(BETA);
			delete doglessMatches[doglessIndex - i];
			_match.ids |= uint96(gammaId << 48);
			_match.doggoOwner = assetToUser[address(GAMMA)][gammaId];
			_match.doggoTokensOwner = dAvail > i ? address(vault) : gammaPos.depositor;
			_match.doglessIndex &= 1;
			GAMMA.transferFrom(address(this), address(smoothOperator), gammaId);
			smoothOperator.bindDoggoToExistingPrimary(primary, _match.ids & 0xffffffffffff, gammaId);
			if (dAvail <= i)
				gammaPos.count--;
			if (gammaPos.count == 0 && dAvail <= i) {
				delete depositPosition[gammaShare][_gammaSpentCounter++];
				gammaPos = getNewDeposit(_gammaSpentCounter, gammaShare, i + 1, toBind);
			}
		}
		gammaSpentCounter = _gammaSpentCounter;
		doglessMatchCounter -= toBind;
		depositPosition[gammaShare][gammaSpentCounter].count = gammaPos.count;
	}

	/**
	 * @notice
	 * Internal function that handles matching Yuga assets with ape coins
	 */
	function _mixExec() internal {
		_mixAndMatch(ALPHA, ALPHA_SHARE, alphaSpentCounter, 1);
		_mixAndMatch(BETA, BETA_SHARE, betaSpentCounter, 0);
		_bindDoggoToMatchId();
	}

	/**
	 * @notice
	 * Internal function that checks requirements of a match
	 * @param _matchId Match ID to check correct requirements
	 */
	function _checkMatch(uint256 _matchId) internal view returns(GreatMatch memory, address[4] memory) {
		GreatMatch memory _match = matches[_matchId];
		address[4] memory adds = [_match.primaryOwner, _match.primaryTokensOwner, _match.doggoOwner,  _match.doggoTokensOwner];
		require(msg.sender == adds[0] || msg.sender == adds[1] ||
				msg.sender == adds[2] || msg.sender == adds[3], "!mtch");
		return(_match, adds);
	}

	/**
	 * @notice
	 * Internal function that handles unbinding a dog from a match
	 * @param _matchId Match ID to remove the dog from
	 * @param _caller Initial caller of this execution
	 */
	function _unbindDoggoFromMatchId(uint256 _matchId, address _caller, uint256 _doglessMatchCounter) internal returns(uint256 totalGamma, uint256 toReturn) {
		GreatMatch storage _match = matches[_matchId];
		address primary = _match.doglessIndex & 1 == 1 ? address(ALPHA) : address(BETA);
		address dogOwner = _match.doggoOwner;
		uint256 ids = _match.ids;
		(totalGamma, toReturn) = smoothOperator.unbindDoggoFromExistingPrimary(
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
		_match.doglessIndex |= uint96(_doglessMatchCounter << 1);
		doglessMatches[_doglessMatchCounter] = _matchId;
		_match.ids = uint96(ids & 0xffffffffffff);
	}

	/**
	 * @notice
	 * Internal function that handles deposits for a user
	 * @param _type Deposit type (bayc/mayc/bakc)
	 * @param _amount Amount of deposits
	 * @param _user User to whom attribute the deposits
	 */
	function _handleDeposit(uint256 _type, uint32 _amount, address _user) internal {
		uint256 depositCounter;
		if (_type == ALPHA_SHARE) {
			depositCounter = alphaDepositCounter++;
			alphaCurrentTotalDeposits += _amount;
		}
		else if (_type == BETA_SHARE) {
			depositCounter = betaDepositCounter++;
			betaCurrentTotalDeposits += _amount;
		}
		else if (_type == GAMMA_SHARE) {
			depositCounter = gammaDepositCounter++;
			gammaCurrentTotalDeposits += _amount;
		}
		depositPosition[_type][depositCounter] =  DepositPosition(_amount, _user);
	}

	/**
	 * @notice
	 * Internal function that handles deposits for a user
	 * @param _share Share type (bayc/mayc/bakc)
	 * @param _depositCounter (bayc/mayc/bakc)
	 * @param _spentCounter bayc/mayc/bakc)
	 * @param _index Index of deposits
	 * @param _amount Amount of deposits to return
	 * @param _user User to whom attribute the deposits
	 */
	function _verifyAndReturnDepositValue(
		uint256 _share,
		uint256 _depositCounter,
		uint256 _spentCounter,
		uint256 _index,
		uint32 _amount,
		address _user) internal returns (uint256){
		uint256 count;
		require(_depositCounter > _index, "!exst");
		require(_spentCounter <= _index, "consmd");
		require(depositPosition[_share][_index].depositor == _user, "!ownr dep");
		count = depositPosition[_share][_index].count;
		require(_amount <= count, "!amt");

		if (_share == ALPHA_SHARE) {
			alphaCurrentTotalDeposits -= _amount;
			if (count == _amount)
				alphaDepositCounter--;
		}
		else if (_share == BETA_SHARE) {
			betaCurrentTotalDeposits -= _amount;
			if (count == _amount)
				betaDepositCounter--;
		}
		else if (_share == GAMMA_SHARE) {
			gammaCurrentTotalDeposits -= _amount;
			if (count == _amount)
				gammaDepositCounter--;
		}

		if (count == _amount) {
			depositPosition[_share][_index] = depositPosition[_share][--_depositCounter];
			delete depositPosition[_share][_depositCounter];
		}
		else
			depositPosition[_share][_index].count -= _amount;
		return _share * _amount;
	}

	/**
	 * @notice
	 * Internal function that deposits NFTs for a user
	 * @param _nft Contract address of the nft
	 * @param _tokenIds Array of token IDs
	 * @param _user User to whom attribute the NFTs
	 */
	function _depositNfts(IERC721Enumerable _nft, uint256[] calldata _tokenIds, address _user) internal {
		uint256 poolId = _nft == ALPHA ? 1 : (_nft == BETA ? 2 : 3);
		for (uint256 i = 0; i < _tokenIds.length; i++) {
			IApeStaking.Position memory pos = APE_STAKING.nftPosition(poolId, _tokenIds[i]);
			require (pos.stakedAmount == 0, "commtd");
			require(_nft.ownerOf(_tokenIds[i]) == _user, "!ownr");
			// EmperorTomatoKetchup, you can't use your #0
			if (poolId == 3 && _tokenIds[i] == 0) revert();
			assetToUser[address(_nft)][_tokenIds[i]] = _user;
			_nft.transferFrom(_user, address(this), _tokenIds[i]);
		}
	}

	/**
	 * @notice
	 * Internal function that withdraws NFTs for a user
	 * @param _nft Contract address of the nft
	 * @param _tokenIds Array of token IDs
	 * @param _user User to whom withdraw the NFTs
	 */
	function _withdrawNfts(IERC721Enumerable _nft, uint256[] calldata _tokenIds, address _user) internal {
		for (uint256 i = 0; i < _tokenIds.length; i++) {
			require(assetToUser[address(_nft)][_tokenIds[i]] == _user, "!ownr");
			delete assetToUser[address(_nft)][_tokenIds[i]];
			_nft.transferFrom(address(this), _user, _tokenIds[i]);
		}
	}

	function _handleFeeAndReturn(uint256 _fee, address _user, uint256 _amountToReturn, bool _fromSmooth) internal {
		if (_fee > 0)
			fee += _fee;
		if (_amountToReturn > 0)
			_handleApeTransfer(_user, _amountToReturn, _fromSmooth);
	}

	function _handleApeTransfer(address _user, uint256 _amountToReturn, bool _fromSmooth) internal {
		if (_user != address(vault)) {
			if (_fromSmooth)
				APE.transferFrom(address(smoothOperator), _user, _amountToReturn);
			else
				vault.withdrawExactAmountOnBehalf(_amountToReturn, _user, _user);
		}
		else {
			smoothOperator.repayDebt(address(vault), _amountToReturn);
			vault.repay(_amountToReturn);
		}
	}

	function _handleSmartReturn(address _depositor, uint256 _share, address _user) internal {
		if (_user != address(vault))
			vault.withdrawExactAmountOnBehalf(_share, _depositor, _user);
		else
			vault.repay(_share);
	}

	function _min(uint256 _a, uint256 _b) internal pure returns (uint256) {
		return _a > _b ? _b : _a;
	}

	/**
	 * @notice
	 * Internal function that fetches the split ratio of a given claim (primary or dog)
	 * @param _claimGamma Boolean that indicates if this is a dog claim or not
	 * @param _weight Value holding the split ratios
	 */
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