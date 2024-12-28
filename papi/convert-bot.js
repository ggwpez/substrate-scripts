import { ApiPromise, WsProvider } from '@polkadot/api';
import { Keyring } from '@polkadot/keyring';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

dotenv.config();

const MILLI_DOT = BigInt(10_000_000);
const MILLI_USDT = BigInt(1_000);
const DOT_ON_HYDRA = 5;
const USDT_ON_HYDRA = 10;
const HDX_ON_HYDRA = 0;
const BTC_ON_HYDRA = 19;
const PHALA_ON_HYDRA = 8;
const GLMR_ON_HYDRA = 16;
const MIN_SWAP_AMOUNT = BigInt(100) * MILLI_DOT;

// Token configuration
const TOKENS = {
	BTC: { id: BTC_ON_HYDRA, ratio: 0.20, omni: false },
	GLMR: { id: GLMR_ON_HYDRA, ratio: 0.20, omni: true },
	PHALA: { id: PHALA_ON_HYDRA, ratio: 0.20, omni: true },
	HDX: { id: HDX_ON_HYDRA, ratio: 0.20, omni: true },
	USDT: { id: USDT_ON_HYDRA, ratio: 0.19, omni: false }, // 1% less for rounding errors
};

// Validate ratios sum to 0.99
const totalRatio = Object.values(TOKENS).reduce((sum, token) => sum + token.ratio, 0);
if (Math.abs(totalRatio - 0.99) > 0.000001) {
	throw new Error('Token ratios must sum to 0.99');
}

const formatDOT = (planks) => {
	planks = BigInt(planks);
	return planks < BigInt(1000) * MILLI_DOT
		? `${Number(planks) / Number(MILLI_DOT)} mDOT`
		: `${Number(planks) / Number(BigInt(1000) * MILLI_DOT)} DOT`;
};

const formatUSDT = (planks) => {
	planks = BigInt(planks);
	return planks < BigInt(1000) * MILLI_USDT
		? `${Number(planks) / Number(MILLI_USDT)} mUSDT`
		: `${Number(planks) / Number(BigInt(1000) * MILLI_USDT)} USDT`;
};

async function connectToChain(url) {
	const provider = new WsProvider(url);
	return await ApiPromise.create({ provider });
}

async function getBalance(api, address) {
	const { data: { free } } = await api.query.system.account(address);
	return free;
}

async function getTokenBalance(api, address, tokenId) {
	if (tokenId == 0) {
		return { free: await getBalance(api, address) };
	}

	return api.query.tokens.accounts(address, tokenId);
}

async function getExistentialDeposit(api) {
	const ed = BigInt(api.consts.balances.existentialDeposit.toNumber());
	if (ed <= 1 || ed == null) throw new Error('Invalid ED');
	return ed;
}

async function waitForBalanceUpdate(api, address, tokenId, initialBalance, timeout = 5 * 600000) {
	const startTime = Date.now();
	while (Date.now() - startTime < timeout) {
		const current = await getTokenBalance(api, address, tokenId);
		if (current.free > initialBalance.free) {
			return current.free - initialBalance.free;
		}
		await new Promise(resolve => setTimeout(resolve, 5000));
	}
	throw new Error('Balance update timeout');
}

async function teleport(api, account, amount) {
	const destination = {
		V4: {
			parents: 0,
			interior: { X1: [{ Parachain: 2034 }] }
		}
	};

	const beneficiary = {
		V4: {
			parents: 0,
			interior: { X1: [{ AccountId32: { network: null, id: account.addressRaw } }] }
		}
	};

	const assets = {
		V4: [{
			id: { Concrete: { parents: 0, interior: 'Here' } },
			fun: { Fungible: amount }
		}]
	};

	return api.tx.xcmPallet
		.limitedReserveTransferAssets(destination, beneficiary, assets, 0, 'Unlimited')
		.signAndSend(account);
}

function construct_swap(api, account, assetIn, assetOut, amount, omni) {
	if (omni) {
		return api.tx.omnipool.sell(assetIn, assetOut, amount, 1)
	} else if (assetOut == USDT_ON_HYDRA) {
		const route = [
			{
				assetIn,
				assetOut: 100,
				pool: { Omnipool: null }
			},
			{
				assetIn: 100,
				assetOut,
				pool: { Stableswap: 100 }
			}
		];

		return api.tx.router.sell(assetIn, assetOut, amount, 1, route)
	} else if (assetOut == BTC_ON_HYDRA) {
		const route = [
			{
				assetIn,
				assetOut: 101,
				pool: { Omnipool: null }
			},
			{
				assetIn: 101,
				assetOut,
				pool: { Stableswap: 101 }
			}
		];

		return api.tx.router.sell(assetIn, assetOut, amount, 1, route)
	}
}

async function swap(api, account, assetIn, assetOut, amount, omni) {
	var promise = new Promise((resolve, _reject) => {
		construct_swap(api, account, assetIn, assetOut, amount, omni)
			.signAndSend(account, ({ status, events }) => {
				if (status.isFinalized) {
					events
						// find/filter for failed events
						.filter(({ event }) =>
							api.events.system.ExtrinsicFailed.is(event)
						)
						// we know that data for system.ExtrinsicFailed is
						// (DispatchError, DispatchInfo)
						.forEach(({ event: { data: [error, info] } }) => {
							if (error.isModule) {
								// for module errors, we have the section indexed, lookup
								const decoded = api.registry.findMetaError(error.asModule);
								const { docs, method, section } = decoded;

								console.error(`Swap error: ${section}.${method}: ${docs.join(' ')}`);
							} else {
								// Other, CannotLookup, BadOrigin, no extra info
								console.error('Swap error:', error.toString());
							}
						});

					resolve();
				}
			});
	});

	return await promise;
}

async function multiSwap(api, account, dotBalance) {
	const results = [];

	for (const [symbol, token] of Object.entries(TOKENS)) {
		const swapAmount = BigInt(Math.floor(Number(dotBalance) * token.ratio));
		if (swapAmount <= 0) continue;

		const initBalance = await getTokenBalance(api, account.address, token.id);
		console.log(`Swapping ${formatDOT(swapAmount)} to ${symbol}`);

		const received_promise = waitForBalanceUpdate(
			api,
			account.address,
			token.id,
			initBalance
		);
		await swap(api, account, DOT_ON_HYDRA, token.id, swapAmount, token.omni);

		var received = 0;
		try {
			received = await received_promise;
		} catch (error) {
			console.error(`Swap failed for ${symbol}:`, error);
		}

		results.push({
			symbol,
			amountIn: swapAmount,
			amountOut: received
		});
	}

	return results;
}

async function setupConnections() {
	const [polkadotApi, hydraApi] = await Promise.all([
		connectToChain(process.env.POLKADOT_URL || 'wss://rpc.polkadot.io'),
		connectToChain(process.env.HYDRA_URL || 'wss://rpc.hydradx.cloud')
	]);

	const account = new Keyring({ type: 'sr25519' }).addFromUri(process.env.CONVERT_BOT_SEED);
	console.log('Account:', account.address);

	return { polkadotApi, hydraApi, account };
}

async function handleDotTeleport(polkadotApi, hydraApi, account, balance, ed) {
	const edPlusFees = ed + (BigInt(100) * MILLI_DOT);
	if (balance <= edPlusFees) {
		console.log(`Balance too low for teleport: ${formatDOT(balance)}`);
		return 0n;
	}

	const teleportAmount = BigInt(balance) - edPlusFees;
	console.log(`Teleporting ${formatDOT(teleportAmount)}`);

	const initDotOnHydra = await getTokenBalance(hydraApi, account.address, DOT_ON_HYDRA);
	const received_promise = waitForBalanceUpdate(
		hydraApi,
		account.address,
		DOT_ON_HYDRA,
		initDotOnHydra
	);
	await teleport(polkadotApi, account, teleportAmount);
	var received = 0;
	try {
		received = await received_promise;
	} catch (error) {
		console.error(`Swap failed for ${symbol}:`, error);
	}
	
	console.log(`Teleported ${formatDOT(received)}`);
	return received;
}

async function main() {
	try {
		const { polkadotApi, hydraApi, account } = await setupConnections();

		const [balance, ed] = await Promise.all([
			getBalance(polkadotApi, account.address),
			getExistentialDeposit(polkadotApi)
		]);
		console.log('Relay balance:', formatDOT(balance));

		await handleDotTeleport(polkadotApi, hydraApi, account, balance, ed);

		const dotBalance = await getTokenBalance(hydraApi, account.address, DOT_ON_HYDRA);
		console.log(`Balance on Hydra: ${formatDOT(dotBalance.free)}`);

		if (dotBalance.free <= MIN_SWAP_AMOUNT) {
			console.log(`Balance is too low for a swap, abort: ${formatDOT(dotBalance.free)}`);
			return;
		}

		console.log(`Swapping ${formatDOT(dotBalance.free)} to multiple tokens`);
		const swapResults = await multiSwap(hydraApi, account, dotBalance.free);

		for (const result of swapResults) {
			console.log(`Swapped ${formatDOT(result.amountIn)} for ${formatUSDT(result.amountOut)} ${result.symbol}`);
		}
	} catch (error) {
		console.error('Error:', error);
	} finally {
		process.exit();
	}
}

main();
