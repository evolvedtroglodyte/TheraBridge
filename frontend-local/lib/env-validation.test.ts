/**
 * Manual test file for environment validation
 *
 * Run with: npx tsx lib/env-validation.test.ts
 */

import { validateEnvironment, logValidationResults } from './env-validation';

async function runTests() {
  console.log('Testing Environment Validation Module\n');

  // Test 1: Normal validation (no health check)
  console.log('Test 1: Basic validation');
  const result1 = await validateEnvironment();
  logValidationResults(result1);

  console.log('\n' + '='.repeat(80) + '\n');

  // Test 2: With health check
  console.log('Test 2: Validation with health check');
  const result2 = await validateEnvironment({
    performHealthCheck: true,
    healthCheckTimeout: 3000,
  });
  logValidationResults(result2);
}

// Run tests
runTests().catch(console.error);
