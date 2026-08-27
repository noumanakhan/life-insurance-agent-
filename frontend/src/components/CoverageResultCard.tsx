import { TrendingUp, Info } from 'lucide-react';
import type { CoverageResult } from '../types';

interface Props {
  result: CoverageResult;
}

function fmtMoney(v: number, currency = 'USD') {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: 0 }).format(v);
}

export default function CoverageResultCard({ result }: Props) {
  const { recommended_coverage, breakdown, assumptions, currency, disclaimer } = result;

  const rows = [
    {
      label: 'Income Replacement',
      sublabel: `${assumptions.income_replacement_years} yrs @ ${(assumptions.real_discount_rate * 100).toFixed(1)}% discount`,
      value: breakdown.discounted_income_replacement,
      color: '#60a5fa',
      positive: true,
    },
    {
      label: 'Total Debt',
      sublabel: 'Mortgage, loans, etc.',
      value: breakdown.total_debt,
      color: '#f59e0b',
      positive: true,
    },
    {
      label: 'Assets Offset',
      sublabel: 'Savings + existing coverage',
      value: breakdown.assets_offset,
      color: '#10b981',
      positive: false,
    },
  ];

  return (
    <div className="glass p-5 fade-in" style={{ borderColor: 'rgba(59,130,246,0.3)' }}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
          <TrendingUp size={16} className="text-blue-400" />
        </div>
        <div>
          <h3 className="font-semibold text-sm">Coverage Recommendation</h3>
          <p className="text-xs" style={{ color: 'var(--c-text-muted)' }}>Deterministic calculation</p>
        </div>
      </div>

      {/* Big number */}
      <div className="text-center py-4 mb-4 rounded-xl" style={{ background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.15)' }}>
        <p className="text-xs font-medium mb-1" style={{ color: 'var(--c-text-muted)' }}>Recommended Coverage</p>
        <p className="text-3xl font-bold gradient-text">{fmtMoney(recommended_coverage, currency)}</p>
      </div>

      {/* Breakdown table */}
      <div className="flex flex-col gap-2 mb-4">
        <p className="text-xs font-semibold uppercase tracking-wider mb-1" style={{ color: 'var(--c-text-muted)' }}>
          Step-by-step breakdown
        </p>
        {rows.map((row) => (
          <div
            key={row.label}
            className="flex items-center justify-between p-3 rounded-lg"
            style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--c-border)' }}
          >
            <div>
              <p className="text-sm font-medium">{row.label}</p>
              <p className="text-xs" style={{ color: 'var(--c-text-muted)' }}>{row.sublabel}</p>
            </div>
            <span
              className="font-semibold text-sm"
              style={{ color: row.color }}
            >
              {row.positive ? '+' : ''}{fmtMoney(row.value, currency)}
            </span>
          </div>
        ))}

        {/* Total line */}
        <div
          className="flex items-center justify-between p-3 rounded-lg"
          style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)' }}
        >
          <p className="font-semibold text-sm">Recommended Total</p>
          <span className="font-bold text-blue-400">{fmtMoney(recommended_coverage, currency)}</span>
        </div>

        <p className="text-xs" style={{ color: 'var(--c-text-muted)' }}>
          Annuity factor: {breakdown.annuity_factor.toFixed(4)}
        </p>
      </div>

      {/* Disclaimer */}
      <div className="flex items-start gap-2 p-3 rounded-lg" style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.15)' }}>
        <Info size={14} className="text-amber-400 mt-0.5 flex-shrink-0" />
        <p className="text-xs" style={{ color: 'var(--c-text-muted)' }}>{disclaimer}</p>
      </div>
    </div>
  );
}
