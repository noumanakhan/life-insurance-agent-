import { User, DollarSign, Users, CreditCard, PiggyBank, Shield, Clock } from 'lucide-react';
import type { ProfileResponse } from '../types';

interface Props {
  profile: ProfileResponse | null;
}

function fmt(val: number | null | undefined, prefix = '$') {
  if (val == null) return null;
  return prefix + val.toLocaleString('en-US', { maximumFractionDigits: 0 });
}

const fields = [
  { key: 'age', label: 'Age', icon: User, format: (v: number) => `${v} yrs` },
  { key: 'annual_income', label: 'Annual Income', icon: DollarSign, format: (v: number) => fmt(v) },
  { key: 'dependents', label: 'Dependents', icon: Users, format: (v: number) => `${v}` },
  { key: 'total_debt', label: 'Total Debt', icon: CreditCard, format: (v: number) => fmt(v) },
  { key: 'available_savings', label: 'Savings', icon: PiggyBank, format: (v: number) => fmt(v) },
  { key: 'existing_life_insurance', label: 'Existing Coverage', icon: Shield, format: (v: number) => fmt(v) },
  { key: 'income_replacement_years', label: 'Replace Years', icon: Clock, format: (v: number) => `${v} yrs` },
];

export default function ProfileSummaryCard({ profile }: Props) {
  const filledCount = profile
    ? fields.filter((f) => profile[f.key as keyof ProfileResponse] != null).length
    : 0;
  const total = fields.length;

  return (
    <div className="glass p-5 flex flex-col gap-4">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-sm" style={{ color: 'var(--c-text)' }}>Client Profile</h3>
          <span className="text-xs" style={{ color: 'var(--c-text-muted)' }}>{filledCount}/{total}</span>
        </div>
        {/* Progress bar */}
        <div className="h-1.5 rounded-full" style={{ background: 'var(--c-border)' }}>
          <div
            className="h-1.5 rounded-full transition-all duration-500"
            style={{
              width: `${(filledCount / total) * 100}%`,
              background: 'linear-gradient(90deg, #3b82f6, #6366f1)',
            }}
          />
        </div>
      </div>

      {/* Fields */}
      <div className="flex flex-col gap-2">
        {fields.map(({ key, label, icon: Icon, format }) => {
          const val = profile?.[key as keyof ProfileResponse];
          const filled = val != null;
          return (
            <div key={key} className={`profile-field ${filled ? 'filled' : ''}`}>
              <Icon
                size={14}
                style={{ color: filled ? 'var(--c-success)' : 'var(--c-text-muted)', flexShrink: 0 }}
              />
              <div className="flex-1 min-w-0">
                <div className="text-xs" style={{ color: 'var(--c-text-muted)' }}>{label}</div>
                <div
                  className="text-sm font-medium truncate"
                  style={{ color: filled ? 'var(--c-text)' : 'var(--c-text-muted)' }}
                >
                  {filled ? (format as (v: number) => string | null)(val as number) : '—'}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {!profile && (
        <p className="text-xs text-center" style={{ color: 'var(--c-text-muted)' }}>
          Start chatting to build your profile
        </p>
      )}
    </div>
  );
}
