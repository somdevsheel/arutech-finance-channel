export type UserRole = "customer" | "employee" | "partner" | "admin";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: AuthUser;
}

export interface AuthSession {
  id: string;
  user_agent: string | null;
  ip_address: string | null;
  created_at: string | null;
  expires_at: string;
}
