// Moralis Solana API Configuration
// Get your API key from: https://admin.moralis.io/

export const MORALIS_CONFIG = {
  SOLANA_GATEWAY: 'https://solana-gateway.moralis.io',
  DEEP_INDEX: 'https://deep-index.moralis.io/api/v2.2',
  // API key should be loaded from environment
  // In Angular, use environment.ts files
};

export interface MoralisConfig {
  apiKey: string;
}

// For development, you can set this here temporarily
// For production, use Angular environment files
export const getMoralisApiKey = (): string => {
  // Try to get from environment or use a default for testing
  if (typeof process !== 'undefined' && process.env?.['MORALIS_API_KEY']) {
    return process.env['MORALIS_API_KEY'];
  }

  // Fallback - should be configured in environment.ts
  console.warn('MORALIS_API_KEY not found in environment. Please configure it.');
  return '';
};

