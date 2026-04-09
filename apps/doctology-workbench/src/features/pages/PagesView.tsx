import { useMemo, useState } from 'react';
import { pageDetails, pages } from '../../lib/mockData';

export function PagesView() {
  const [selectedId, setSelectedId] = useState(pages[0].id);
  const page = pageDetails[selectedId] ?? pageDetails['doctology-ui'];
  const selected = useMemo(() => pages.find((item) => item.id === selectedId), [selectedId]);

  return (
    <div className="content-grid page-grid">
      <aside className="card panel-section page-list-panel">
        <div className="eyebrow">Pages</div>
        <h3 className="panel-title">Private Wikipedia surface</h3>
        <ul className="page-list">
          {pages.map((item) => (
            <li key={item.id}>
              <button
                className={`page-list__item ${item.id === selectedId ? 'page-list__item--active' : ''}`}
                onClick={() => setSelectedId(item.id)}
              >
                <span>{item.title}</span>
                <small>{item.type}</small>
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <article className="card panel-section article-panel">
        <div className="eyebrow">{page.kicker}</div>
        <h2 className="section-title">{page.title}</h2>
        <p className="section-copy">{page.summary}</p>
        {page.sections.map((section) => (
          <section key={section.heading} className="article-section">
            <h3>{section.heading}</h3>
            {section.body.map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
          </section>
        ))}
      </article>

      <aside className="card panel-section context-panel">
        <h3 className="panel-title">Context rail</h3>
        <div className="context-block">
          <div className="context-label">Updated</div>
          <div>{selected?.updatedAt}</div>
        </div>
        <div className="context-block">
          <div className="context-label">Related pages</div>
          <ul className="link-list">
            {page.relatedPages.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="context-block">
          <div className="context-label">Provenance</div>
          <ul className="link-list">
            {page.provenance.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </aside>
    </div>
  );
}
