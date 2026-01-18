export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api',
  // Add other runtime config keys your app expects, e.g.:
  // analyticsKey: '',
  // firebase: { ... }
};

export type Environment = typeof environment;