const ACCESS_TOKEN_KEY = 'therapybridge_access_token';
const REFRESH_TOKEN_KEY = 'therapybridge_refresh_token';

export const tokenStorage = {
  /**
   * Save both access and refresh tokens to localStorage.
   */
  saveTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  },

  /**
   * Get access token from localStorage.
   * Returns null if not found.
   */
  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  /**
   * Get refresh token from localStorage.
   * Returns null if not found.
   */
  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  /**
   * Remove both tokens from localStorage (logout).
   */
  clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  /**
   * Check if user has tokens (quick auth check).
   * Note: Does NOT validate if tokens are valid/expired.
   */
  hasTokens(): boolean {
    return !!(this.getAccessToken() && this.getRefreshToken());
  }
};
