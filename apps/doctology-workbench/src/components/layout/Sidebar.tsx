import { NavLink } from 'react-router-dom';

const items = [
  { to: '/dashboard', label: 'Dashboard', short: 'DB' },
  { to: '/ask', label: 'Ask / Explore', short: 'Q' },
  { to: '/pages', label: 'Pages', short: 'PG' },
  { to: '/graph', label: 'Graph Inspect', short: 'GR' },
  { to: '/doctor', label: 'Doctor', short: 'DR' }
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand-block">
        <div className="brand-mark">D</div>
        <div>
          <div className="brand-title">DocTology</div>
          <div className="brand-subtitle">Knowledge Workbench</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-item ${isActive ? 'nav-item--active' : ''}`}
          >
            <span className="nav-item__short">{item.short}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-section">
        <div className="sidebar-section__title">Current focus</div>
        <p>Keep graph projection derived, keep wiki readable, keep operator health visible.</p>
      </div>
    </aside>
  );
}
