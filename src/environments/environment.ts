export const environment = {
  production: false,
  apiUrl: 'http://localhost:3000',
  // Add other runtime config keys your app expects, e.g.:
  // analyticsKey: '',
  // firebase: { ... }
};

export type Environment = typeof environment;