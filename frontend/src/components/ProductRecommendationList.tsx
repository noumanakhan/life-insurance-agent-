import { Building2, Clock, DollarSign, ArrowRight } from 'lucide-react';
import type { Product } from '../types';

interface Props {
  products: Product[];
}

const typeColors: Record<string, string> = {
  term: 'rgba(59,130,246,0.15)',
  whole: 'rgba(16,185,129,0.15)',
  universal: 'rgba(139,92,246,0.15)',
};

const typeBorders: Record<string, string> = {
  term: 'rgba(59,130,246,0.25)',
  whole: 'rgba(16,185,129,0.25)',
  universal: 'rgba(139,92,246,0.25)',
};

const typeLabels: Record<string, string> = {
  term: 'Term Life',
  whole: 'Whole Life',
  universal: 'Universal Life',
};

function fmtMoney(v: number | null) {
  if (v == null) return 'N/A';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(v);
}

export default function ProductRecommendationList({ products }: Props) {
  if (!products || products.length === 0) return null;

  return (
    <div className="mt-3 flex flex-col gap-3">
      <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--c-text-muted)' }}>
        Matching Products
      </p>
      {products.map((p) => {
        const type = p.product_type || 'term';
        return (
          <div
            key={p.id}
            className="p-4 rounded-xl fade-in"
            style={{
              background: typeColors[type] || 'rgba(59,130,246,0.1)',
              border: `1px solid ${typeBorders[type] || 'rgba(59,130,246,0.2)'}`,
            }}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-2">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Building2 size={13} style={{ color: 'var(--c-text-muted)' }} />
                  <span className="text-xs" style={{ color: 'var(--c-text-muted)' }}>{p.insurer_name}</span>
                </div>
                <p className="font-semibold text-sm">{p.product_name}</p>
              </div>
              <span
                className="text-xs font-medium px-2 py-1 rounded-full"
                style={{ background: typeBorders[type], color: 'var(--c-text)' }}
              >
                {typeLabels[type] || type}
              </span>
            </div>

            {/* Details grid */}
            <div className="grid grid-cols-2 gap-2 mt-3">
              <div className="flex items-center gap-2">
                <DollarSign size={12} style={{ color: 'var(--c-text-muted)' }} />
                <div>
                  <p className="text-xs" style={{ color: 'var(--c-text-muted)' }}>Coverage</p>
                  <p className="text-xs font-medium">{fmtMoney(p.min_coverage)} – {fmtMoney(p.max_coverage)}</p>
                </div>
              </div>
              {p.term_years && (
                <div className="flex items-center gap-2">
                  <Clock size={12} style={{ color: 'var(--c-text-muted)' }} />
                  <div>
                    <p className="text-xs" style={{ color: 'var(--c-text-muted)' }}>Term</p>
                    <p className="text-xs font-medium">{p.term_years} years</p>
                  </div>
                </div>
              )}
              {p.premium_estimate && (
                <div className="flex items-center gap-2 col-span-2">
                  <ArrowRight size={12} style={{ color: 'var(--c-text-muted)' }} />
                  <p className="text-xs" style={{ color: 'var(--c-text-muted)' }}>
                    Est. premium: <span style={{ color: 'var(--c-text)' }} className="font-medium">{fmtMoney(p.premium_estimate)}/mo</span>
                  </p>
                </div>
              )}
            </div>

            {p.description && (
              <p className="text-xs mt-2" style={{ color: 'var(--c-text-muted)' }}>{p.description}</p>
            )}
          </div>
        );
      })}
    </div>
  );
}
