import type { GraphInspectPayload, GraphInspectSeed } from "../lib/api";

type GraphInspectPanelProps = {
  seeds: GraphInspectSeed[];
  activeSeedKey: string | null;
  inspect: GraphInspectPayload | null;
  loading: boolean;
  error: string | null;
  onInspect: (seed: GraphInspectSeed) => void;
};

export function GraphInspectPanel({
  seeds,
  activeSeedKey,
  inspect,
  loading,
  error,
  onInspect,
}: GraphInspectPanelProps) {
  return (
    <div className="graph-inspect-panel">
      <section className="message-panel">
        <p className="eyebrow">Seeded graph inspect</p>
        {seeds.length ? (
          <div className="graph-seed-list" role="list">
            {seeds.map((seed) => {
              const active = seed.key === activeSeedKey;
              return (
                <button
                  key={seed.key}
                  type="button"
                  className={`graph-seed-button ${active ? "graph-seed-button-active" : ""}`}
                  onClick={() => onInspect(seed)}
                  disabled={loading}
                >
                  <strong>{seed.title}</strong>
                  <span>{seed.subtitle}</span>
                </button>
              );
            })}
          </div>
        ) : (
          <p className="panel-copy">No page, source, or claim seed is available yet. Open a page or source first.</p>
        )}
      </section>

      <section className="message-panel">
        <p className="eyebrow">Graph result</p>
        {loading ? <p className="panel-copy">Loading bounded neighborhood…</p> : null}
        {error ? <p className="error-copy">{error}</p> : null}
        {inspect ? (
          <>
            <p className="panel-copy">{inspect.summary}</p>
            <div className="graph-metrics" role="list">
              <div className="evidence-card">
                <span>node count</span>
                <strong>{inspect.neighborhood.node_count}</strong>
              </div>
              <div className="evidence-card">
                <span>edge count</span>
                <strong>{inspect.neighborhood.edge_count}</strong>
              </div>
            </div>
            {inspect.mode === "available" ? (
              <>
                <ul className="compact-list compact-list-plain detail-list graph-node-list">
                  {inspect.neighborhood.nodes.map((node) => (
                    <li key={node.id}>
                      <strong>{node.label}</strong>
                      <span> — {node.kind}{node.matched ? " · seed match" : ""}</span>
                    </li>
                  ))}
                </ul>
                {inspect.path_hints.length ? (
                  <ul className="compact-list compact-list-plain detail-list graph-edge-list">
                    {inspect.path_hints.map((hint) => (
                      <li key={hint}>{hint}</li>
                    ))}
                  </ul>
                ) : null}
              </>
            ) : (
              <p className="panel-copy">No bounded neighborhood is available yet.</p>
            )}
          </>
        ) : (
          <p className="panel-copy">Choose a seed to inspect the derived graph surface.</p>
        )}
      </section>
    </div>
  );
}
