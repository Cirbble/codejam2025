/**
 * Known token mint addresses for PumpPortal integration
 * Add token addresses here as they are discovered
 */
export const TOKEN_ADDRESSES: Record<string, string> = {
  // HEGE token address (found via DexScreener)
  'HEGE': 'ULwSJmmpxmnRfpu6BjnK6rprKXqD5jXUmPpS1FxHXFy',
  
  // Example format:
  // 'TOKEN_SYMBOL': 'mint_address_here'
};

/**
 * Get token address by symbol
 */
export function getTokenAddress(symbol: string): string | undefined {
  return TOKEN_ADDRESSES[symbol.toUpperCase()];
}
