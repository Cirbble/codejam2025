/**
 * Server-side configuration loader
 *
 * NOTE: This file is designed for SSR/server-side usage only.
 * Environment variables are loaded server-side via process.env
 *
 * For Angular browser context:
 * - Create a backend API endpoint to fetch config
 * - Or manually inject API keys via setApiKey() methods
 */

/**
 * Check if running on server
 */
export function isServer(): boolean {
  return typeof window === 'undefined';
}

/**
 * Server configuration interface
 */
interface ServerConfig {
  moralisApiKey: string;
  browserCashApiKey: string;
  agentCashApiKey: string;
  solanaPrivateKey: string;
}

/**
 * Get server config (only works server-side)
 * Returns empty strings if called from browser
 */
export function getServerConfig(key: keyof ServerConfig): string {
  // Only try to access process.env if we're on the server
  if (!isServer()) {
    console.warn('getServerConfig() called from browser context - returning empty string');
    return '';
  }

  // Server-side only - access process.env
  const config: ServerConfig = {
    moralisApiKey: process.env['MORALIS_API_KEY'] || '',
    browserCashApiKey: process.env['BROWSER_CASH_API_KEY'] || '',
    agentCashApiKey: process.env['AGENT_CASH_API_KEY'] || '',
    solanaPrivateKey: process.env['SOLANA_PRIVATE_KEY'] || '',
  };

  return config[key];
}

/**
 * Get all server config (only works server-side)
 */
export function getAllServerConfig(): ServerConfig {
  if (!isServer()) {
    console.warn('getAllServerConfig() called from browser context - returning empty config');
    return {
      moralisApiKey: '',
      browserCashApiKey: '',
      agentCashApiKey: '',
      solanaPrivateKey: '',
    };
  }

  return {
    moralisApiKey: process.env['MORALIS_API_KEY'] || '',
    browserCashApiKey: process.env['BROWSER_CASH_API_KEY'] || '',
    agentCashApiKey: process.env['AGENT_CASH_API_KEY'] || '',
    solanaPrivateKey: process.env['SOLANA_PRIVATE_KEY'] || '',
  };
}

