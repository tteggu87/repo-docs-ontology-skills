export function AskPage() {
  return (
    <div className="screen-stack">
      <section className="card ask-composer">
        <div>
          <div className="eyebrow">Ask / Explore</div>
          <h2 className="section-title">Ask from wiki first, verify with canonical truth.</h2>
        </div>
        <textarea className="query-box" defaultValue="What changed in the graph-vs-baseline evaluation for DocTology?" />
        <div className="button-row">
          <button className="primary-button">Run grounded answer</button>
          <button className="ghost-button">Open graph neighborhood</button>
        </div>
      </section>

      <section className="content-grid ask-grid">
        <article className="card panel-section">
          <h3 className="panel-title">Answer bundle</h3>
          <p className="answer-copy">
            Graph inspect remains useful as a drill-down surface, but the main product value still comes from dashboard trust,
            page readability, and provenance-aware answers.
          </p>
          <div className="info-row"><span>Route used</span><strong>wiki → canonical verify → graph note</strong></div>
          <div className="info-row"><span>Uncertainty</span><strong>No blocking validator failure detected</strong></div>
        </article>

        <article className="card panel-section">
          <h3 className="panel-title">Evidence & related pages</h3>
          <ul className="link-list">
            <li>DocTology UI and dashboard direction</li>
            <li>DocTology UI sharpened design</li>
            <li>Mem0 graph + wiki + lg-ontology synthesis</li>
          </ul>
        </article>
      </section>
    </div>
  );
}
