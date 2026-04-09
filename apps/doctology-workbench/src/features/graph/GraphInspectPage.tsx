import { graphEdges, graphNodes } from '../../lib/mockData';

export function GraphInspectPage() {
  return (
    <div className="screen-stack">
      <section className="card graph-header">
        <div>
          <div className="eyebrow">Graph Inspect</div>
          <h2 className="section-title">Seeded neighborhood, never the whole graph.</h2>
          <p className="section-copy">
            This bounded graph panel is intentionally read-only and derived. Use it to inspect why things connect, not to define truth.
          </p>
        </div>
        <div className="button-row">
          <button className="ghost-button">1 hop</button>
          <button className="ghost-button">2 hops</button>
          <button className="primary-button">Focus selected path</button>
        </div>
      </section>

      <section className="content-grid graph-grid">
        <article className="card panel-section graph-canvas-panel">
          <div className="graph-canvas">
            {graphNodes.map((node, index) => (
              <div
                key={node.id}
                className={`graph-node graph-node--${node.family.toLowerCase()} ${node.emphasis ? 'graph-node--active' : ''}`}
                style={{ left: `${10 + (index % 3) * 28}%`, top: `${18 + Math.floor(index / 3) * 28}%` }}
              >
                <span>{node.label}</span>
              </div>
            ))}
            <div className="graph-overlay-note">WebGL-capable renderer adapter plugs in here later.</div>
          </div>
        </article>

        <aside className="card panel-section">
          <h3 className="panel-title">Graph controls</h3>
          <ul className="link-list">
            <li>Seed required</li>
            <li>Node caps enforced</li>
            <li>Edge family filters</li>
            <li>List fallback for oversize neighborhoods</li>
          </ul>
          <h3 className="panel-title space-top">Current edge families</h3>
          <ul className="link-list">
            {Array.from(new Set(graphEdges.map((edge) => edge.family))).map((edge) => (
              <li key={edge}>{edge}</li>
            ))}
          </ul>
        </aside>
      </section>
    </div>
  );
}
