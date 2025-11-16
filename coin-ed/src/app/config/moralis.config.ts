// Moralis Solana API Configuration
// API key is loaded from .env file (same as Browser Cash API keys)

export const MORALIS_CONFIG = {
  SOLANA_GATEWAY: 'https://solana-gateway.moralis.io',
  DEEP_INDEX: 'https://deep-index.moralis.io/api/v2.2',
};

/**
 * Get Moralis API key from environment
 * The key is stored in .env file alongside other API keys
 */
export const getMoralisApiKey = (): string => {
  // In Angular, we can't directly access process.env in the browser
  // Instead, we'll load it from the server or use a configuration service
  // For now, return empty string - the service will need the key passed to it
  // or loaded via a backend endpoint

  // Note: For production, inject the API key via:
  // 1. Backend endpoint that reads from .env
  // 2. Build-time injection
  // 3. Server-side configuration service

  return '';
};

/**
 * In Angular, to use .env variables in the frontend:
 *
 * Option 1: Create a backend endpoint that returns config
 * Option 2: Use Angular environment replacements during build
 * Option 3: Load via server-side rendering (SSR)
 *
 * Since this project uses SSR and has .env files, the best approach
 * is to create a config endpoint or inject during SSR.
 */


