// ── API types ─────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
}

export interface SessionResponse {
  id: string;
  user_id: string;
  title: string | null;
  created_at: string;
}

export interface MessageResponse {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  tool_calls_json: string | null;
  created_at: string;
}

export interface ToolCallInfo {
  name: string;
  args: Record<string, unknown>;
  result: unknown;
}

export interface ChatResponse {
  reply: string;
  session_id: string;
  profile_updated: boolean;
  tool_calls: ToolCallInfo[];
}

export interface ProfileResponse {
  session_id: string;
  age: number | null;
  annual_income: number | null;
  dependents: number | null;
  total_debt: number | null;
  available_savings: number | null;
  existing_life_insurance: number | null;
  income_replacement_years: number;
  currency: string;
}

export interface CoverageBreakdown {
  discounted_income_replacement: number;
  annuity_factor: number;
  total_debt: number;
  assets_offset: number;
  raw_before_floor: number;
}

export interface CoverageResult {
  recommended_coverage: number;
  breakdown: CoverageBreakdown;
  assumptions: { income_replacement_years: number; real_discount_rate: number };
  currency: string;
  disclaimer: string;
}

export interface Citation {
  document: string;
  page: number | null;
  excerpt: string;
}

export interface PolicyQAResponse {
  answer: string;
  citations: Citation[];
  disclaimer: string;
}

export interface Product {
  id: string;
  insurer_name: string | null;
  product_name: string | null;
  product_type: string | null;
  min_coverage: number | null;
  max_coverage: number | null;
  term_years: number | null;
  premium_estimate: number | null;
  currency: string;
  region: string | null;
  description: string | null;
}
