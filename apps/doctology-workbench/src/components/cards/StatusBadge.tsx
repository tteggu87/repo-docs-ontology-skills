import type { StatusTone } from '../../lib/types';

const toneClass: Record<StatusTone, string> = {
  fresh: 'badge badge-fresh',
  healthy: 'badge badge-healthy',
  warning: 'badge badge-warning',
  danger: 'badge badge-danger',
  derived: 'badge badge-derived'
};

export function StatusBadge({ tone = 'healthy', children }: { tone?: StatusTone; children: React.ReactNode }) {
  return <span className={toneClass[tone]}>{children}</span>;
}
