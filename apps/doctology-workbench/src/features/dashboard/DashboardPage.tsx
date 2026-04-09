import { StatCard } from '../../components/cards/StatCard';
import { dashboardKpis, recentActivity, suggestedActions } from '../../lib/mockData';

export function DashboardPage() {
  return (
    <div className="screen-stack">
      <section className="hero-panel card">
        <div>
          <div className="eyebrow">Dashboard</div>
          <h2 className="section-title">Trust the pipeline before you trust the graph.</h2>
          <p className="section-copy">
            Monitor freshness, canonical health, pending review, and where graph expansion is genuinely helping.
          </p>
        </div>
        <button className="primary-button">Run refresh report</button>
      </section>

      <section className="kpi-grid">
        {dashboardKpis.map((item) => (
          <StatCard key={item.label} {...item} />
        ))}
      </section>

      <section className="content-grid">
        <article className="card panel-section">
          <h3 className="panel-title">Recent activity</h3>
          <ul className="activity-list">
            {recentActivity.map((item) => (
              <li key={item.title} className="activity-item">
                <div className="activity-item__title">{item.title}</div>
                <div className="activity-item__meta">{item.meta}</div>
                <p>{item.detail}</p>
              </li>
            ))}
          </ul>
        </article>

        <article className="card panel-section">
          <h3 className="panel-title">Suggested next actions</h3>
          <ul className="activity-list compact">
            {suggestedActions.map((item) => (
              <li key={item.title} className="activity-item">
                <div className="activity-item__title">{item.title}</div>
                <div className="activity-item__meta">{item.meta}</div>
                <p>{item.detail}</p>
              </li>
            ))}
          </ul>
        </article>
      </section>
    </div>
  );
}
