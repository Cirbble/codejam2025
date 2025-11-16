/**
 * Server-side configuration loader
 * Reads environment variables from .env file (server-side only)
 *
 * This file should only be used in server-side context (SSR, API routes)
 * For client-side, use the config endpoint or inject during SSR
 */

import { config } from 'dotenv';
import { join } from 'path';

// Load .env from parent directory (coin-ed/scrapper_and_analysis/.env)
const envPath = join(process.cwd(), 'scrapper_and_analysis', '.env');
config({ path: envPath });

// Also try loading from project root
const rootEnvPath = join(process.cwd(), '..', '.env');
config({ path: rootEnvPath });

export const serverConfig = {
  moralisApiKey: process.env['MORALIS_API_KEY'] || '',
  browserCashApiKey: process.env['BROWSER_CASH_API_KEY'] || '',
  agentCashApiKey: process.env['AGENT_CASH_API_KEY'] || '',
  solanaPrivateKey: process.env['SOLANA_PRIVATE_KEY'] || '',
};

/**
 * Get config value by key
 */
export function getServerConfig(key: keyof typeof serverConfig): string {
  return serverConfig[key];
}

/**
 * Check if running on server
 */
export function isServer(): boolean {
  return typeof window === 'undefined';
}

