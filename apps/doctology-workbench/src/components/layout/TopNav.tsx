export function TopNav() {
  return (
    <header className="topnav">
      <div>
        <div className="eyebrow">Private ontology / wiki operations</div>
        <h1 className="topnav__title">Calm SaaS dashboard for DocTology</h1>
      </div>
      <div className="topnav__actions">
        <input className="search-input" placeholder="Search pages, entities, or seed ids" />
        <button className="ghost-button">Projection status</button>
      </div>
    </header>
  );
}
