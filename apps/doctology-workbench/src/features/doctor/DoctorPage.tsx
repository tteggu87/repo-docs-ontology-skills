export function DoctorPage() {
  return (
    <div className="screen-stack">
      <section className="content-grid doctor-grid">
        <article className="card panel-section">
          <div className="eyebrow">Doctor</div>
          <h2 className="section-title">Operational trust surface</h2>
          <ul className="activity-list compact">
            <li className="activity-item">
              <div className="activity-item__title">Projection freshness warning</div>
              <p>Graph projection is one refresh behind canonical accepted claims.</p>
            </li>
            <li className="activity-item">
              <div className="activity-item__title">Validator summary</div>
              <p>No hard failure, but docs/runtime alignment should be re-checked after graph export.</p>
            </li>
          </ul>
        </article>

        <article className="card panel-section">
          <h3 className="panel-title">Recommended repair commands</h3>
          <div className="command-block">python scripts/doctology_ui_report.py --repo-root .</div>
          <div className="command-block">python lg-ontology/scripts/export_graph_projection.py --repo-root .</div>
          <div className="command-block">python lg-ontology/scripts/compare_graph_modes.py --repo-root . --query "DocTology"</div>
        </article>
      </section>
    </div>
  );
}
