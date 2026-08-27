import { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp } from 'lucide-react';
import type { Citation } from '../types';

interface Props {
  citations: Citation[];
}

export default function PolicyCitation({ citations }: Props) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-3 flex flex-col gap-2">
      <p className="text-xs font-medium" style={{ color: 'var(--c-text-muted)' }}>
        Sources
      </p>
      <div className="flex flex-wrap gap-2">
        {citations.map((c, i) => (
          <div key={i} className="w-full">
            <button
              className="citation-chip"
              onClick={() => setExpanded(expanded === i ? null : i)}
            >
              <BookOpen size={10} />
              {c.document}{c.page ? ` · p.${c.page}` : ''}
              {expanded === i ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
            </button>

            {expanded === i && (
              <div
                className="mt-2 p-3 rounded-lg text-xs fade-in"
                style={{
                  background: 'rgba(99,102,241,0.08)',
                  border: '1px solid rgba(99,102,241,0.2)',
                  color: 'var(--c-text-muted)',
                  lineHeight: '1.6',
                }}
              >
                "{c.excerpt}…"
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
