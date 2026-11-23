export const environment = {
  production: false,
  apiUrl: 'http://127.0.0.1:8000/api',
  // Add other runtime config keys your app expects, e.g.:
  // analyticsKey: '',
  // firebase: { ... }
};

export type Environment = typeof environment;
