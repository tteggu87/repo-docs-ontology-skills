import type { Kpi } from '../../lib/types';
import { StatusBadge } from './StatusBadge';

export function StatCard({ label, value, hint, tone = 'healthy' }: Kpi) {
  return (
    <article className="card stat-card">
      <div className="stat-card__header">
        <span className="stat-card__label">{label}</span>
        <StatusBadge tone={tone}>{tone}</StatusBadge>
      </div>
      <div className="stat-card__value">{value}</div>
      <p className="stat-card__hint">{hint}</p>
    </article>
  );
}
