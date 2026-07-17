export type UserRole = "customer" | "employee" | "partner" | "admin";

export interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  is_system: boolean;
}

export interface Permission {
  id: string;
  code: string;
  description: string;
}

export type LenderType = "bank" | "nbfc";

export interface Lender {
  id: string;
  name: string;
  type: LenderType;
  code: string;
  contact_email: string | null;
  contact_phone: string | null;
  commission_rate_percent: string;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface LoanProduct {
  id: string;
  slug: string;
  name: string;
  interest_rate_min: string;
  interest_rate_max: string;
  tenure_min_months: number;
  tenure_max_months: number;
  amount_min: number;
  amount_max: number;
  documents_required: string[];
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export type NotificationChannel = "email" | "sms" | "whatsapp";

export interface NotificationTemplate {
  id: string;
  code: string;
  channel: NotificationChannel;
  subject: string | null;
  body: string;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface BlogSection {
  heading: string | null;
  paragraphs: string[];
}

export interface BlogPost {
  id: string;
  slug: string;
  title: string;
  excerpt: string;
  author: string;
  reading_minutes: number;
  sections: BlogSection[];
  tags: string[];
  is_published: boolean;
  published_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export type SettingValueType = "string" | "boolean" | "number";

export interface SystemSetting {
  id: string;
  key: string;
  value: string;
  value_type: SettingValueType;
  description: string;
  updated_at: string | null;
}

export interface AuditLogEntry {
  id: string;
  actor_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  extra_metadata: Record<string, unknown> | null;
  created_at: string;
}
