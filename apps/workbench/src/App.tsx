import { startTransition, useEffect, useState } from "react";
import { BookOpenText, LayoutDashboard, Search } from "lucide-react";
import DOMPurify from "dompurify";
import { marked } from "marked";
import {
  draftSourceSummary,
  fetchQueryPreview,
  fetchSourceDetail,
  fetchWorkbenchReview,
  fetchWarehouseSummary,
  fetchWikiIndex,
  fetchWikiPage,
  fetchWorkbenchSummary,
  reviewClaim,
  runWorkbenchAction,
  saveAnalysis,
  type DraftSourceSummaryPayload,
  type QueryPreviewPayload,
  type ReviewClaimPayload,
  type SaveAnalysisPayload,
  type SourceDetailPayload,
  type WarehouseSummaryPayload,
  type WorkbenchActionKey,
  type WorkbenchActionPayload,
  type WorkbenchReviewPayload,
  type WikiIndexPayload,
  type WikiPagePayload,
  type WorkbenchSummary,
} from "./lib/api";
import { buildGraphSurface } from "./lib/graph";

type SectionId = "home" | "ask" | "wiki" | "sources" | "review" | "warehouse" | "doctor" | "graph";
type PageFilterId =
  | "all"
  | "sources"
  | "analyses"
  | "concepts"
  | "entities"
  | "people"
  | "projects"
  | "timelines";

type SectionConfig = {
  id: SectionId;
  label: string;
  eyebrow: string;
  title: string;
  description: string;
  icon: typeof Search;
  rail: "primary" | "advanced";
};

function isSectionId(value: string): value is SectionId {
  return (
    value === "home" ||
    value === "ask" ||
    value === "wiki" ||
    value === "sources" ||
    value === "review" ||
    value === "warehouse" ||
    value === "doctor" ||
    value === "graph"
  );
}

function sectionFromHash(hash: string): SectionId {
  const candidate = hash.replace(/^#/, "");
  return isSectionId(candidate) ? candidate : "home";
}

function pageFilterLabel(value: PageFilterId): string {
  const labels: Record<PageFilterId, string> = {
    all: "전체",
    sources: "소스",
    analyses: "분석",
    concepts: "개념",
    entities: "엔티티",
    people: "인물",
    projects: "프로젝트",
    timelines: "타임라인",
  };
  return labels[value];
}

function sectionNameLabel(value: string): string {
  const labels: Record<string, string> = {
    Meta: "메타",
    Sources: "소스",
    Analyses: "분석",
    Concepts: "개념",
    Entities: "엔티티",
    People: "인물",
    Projects: "프로젝트",
    Timelines: "타임라인",
    sources: "소스",
    analyses: "분석",
    concepts: "개념",
    entities: "엔티티",
    people: "인물",
    projects: "프로젝트",
    timelines: "타임라인",
    wiki: "위키",
  };
  return labels[value] ?? value;
}

function coverageLabel(value: string): string {
  const labels: Record<string, string> = {
    none: "근거 없음",
    thin: "근거 얕음",
    supported: "근거 확보",
    ready: "준비됨",
  };
  return labels[value] ?? value;
}

function warningLabel(value: string): string {
  const labels: Record<string, string> = {
    empty_query: "질문이 비어 있습니다.",
    thin_coverage: "근거가 얕아서 결과를 검토용 초안으로 다뤄야 합니다.",
    no_direct_matches: "직접적으로 맞는 근거를 찾지 못했습니다.",
  };
  return labels[value] ?? value.replaceAll("_", " ");
}

function renderMarkdown(markdown: string) {
  return DOMPurify.sanitize(marked.parse(markdown) as string);
}

const sections: SectionConfig[] = [
  {
    id: "home",
    label: "홈",
    eyebrow: "시작하기",
    title: "LLM Wiki 시작 화면",
    description: "지금 할 일을 먼저 고르고, 그다음 실제 작업 레인으로 들어갑니다.",
    icon: LayoutDashboard,
    rail: "primary",
  },
  {
    id: "ask",
    label: "질문",
    eyebrow: "근거 기반 질문",
    title: "위키에 질문하기",
    description: "로컬 위키를 먼저 검색하고, 근거를 확인한 뒤, 남길 가치가 있는 답변만 분석 페이지로 저장합니다.",
    icon: Search,
    rail: "primary",
  },
  {
    id: "wiki",
    label: "위키",
    eyebrow: "문서 탐색",
    title: "위키 읽기",
    description: "제목 중심 목록으로 페이지를 탐색하고, 관련 개념·인물·소스·분석 문서를 빠르게 이어서 확인합니다.",
    icon: BookOpenText,
    rail: "primary",
  },
  {
    id: "sources",
    label: "소스",
    eyebrow: "업데이트 레인",
    title: "소스 검토와 초안 만들기",
    description: "소스별 coverage, review queue, incremental status를 확인하고 draft-only 요약 초안을 만듭니다.",
    icon: BookOpenText,
    rail: "primary",
  },
  {
    id: "review",
    label: "검토",
    eyebrow: "운영 검토",
    title: "리뷰 큐 확인하기",
    description: "low coverage, stale, uncertainty, low-confidence claims를 묶어서 검토하고 triage합니다.",
    icon: Search,
    rail: "advanced",
  },
  {
    id: "warehouse",
    label: "창고",
    eyebrow: "Canonical inspection",
    title: "Warehouse 확인하기",
    description: "canonical registry count와 sample preview를 읽기 전용으로 확인합니다.",
    icon: BookOpenText,
    rail: "advanced",
  },
  {
    id: "doctor",
    label: "닥터",
    eyebrow: "Audited actions",
    title: "Doctor 실행하기",
    description: "status, reindex, lint를 명시적으로 실행하고 구조화된 결과만 확인합니다.",
    icon: Search,
    rail: "advanced",
  },
  {
    id: "graph",
    label: "그래프",
    eyebrow: "Derived inspect",
    title: "Graph inspect mode",
    description: "graph는 seed-required, bounded, read-only inspect surface로만 노출합니다.",
    icon: Search,
    rail: "advanced",
  },
];

const starterQuestions = [
  "이 작업공간이 ontology builders에 대해 현재 무엇을 알고 있나?",
  "이 저장소의 핵심 오픈 퀘스천은 무엇인가?",
  "현재 위키에서 가장 강한 주제들을 요약해줘",
];

function RelatedPageList(props: {
  title: string;
  pages: { stem: string; title: string; summary: string; section: string }[];
  onOpen: (stem: string) => void;
}) {
  if (!props.pages.length) {
    return null;
  }

  return (
    <section className="side-card">
      <h3>{props.title}</h3>
      <ul className="compact-list compact-list-plain">
        {props.pages.map((item) => (
          <li key={item.stem}>
            <button type="button" className="link-button" onClick={() => props.onOpen(item.stem)}>
              {item.title}
            </button>
            <span>{item.summary}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function SaveResultPanel(props: {
  saveResult: SaveAnalysisPayload;
  onOpenAnalysis: (stem: string) => void;
}) {
  return (
    <section className="save-result-panel">
      <div className="save-result-header">
        <div>
          <p className="eyebrow">저장 완료</p>
          <h4>{props.saveResult.analysis_path}</h4>
        </div>
        <button type="button" className="ghost-button" onClick={() => props.onOpenAnalysis(props.saveResult.analysis_stem)}>
          저장한 분석 열기
        </button>
      </div>
      <div className="save-result-grid">
        <div className="save-result-card">
          <span>변경 파일</span>
          <strong>{props.saveResult.changed_files.length}</strong>
        </div>
        <div className="save-result-card">
          <span>연결된 페이지</span>
          <strong>{props.saveResult.linked_pages.length}</strong>
        </div>
      </div>
      <div className="save-result-lists">
        <div>
          <h5>Changed files</h5>
          <ul className="compact-list compact-list-plain detail-list">
            {props.saveResult.changed_files.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div>
          <h5>Linked pages</h5>
          <ul className="compact-list compact-list-plain detail-list">
            {props.saveResult.linked_pages.length ? (
              props.saveResult.linked_pages.map((item) => <li key={item}>{item}</li>)
            ) : (
              <li>이번 저장에서는 추가 링크백이 없었습니다.</li>
            )}
          </ul>
        </div>
      </div>
    </section>
  );
}

export default function App() {
  const [activeSection, setActiveSection] = useState<SectionId>(() =>
    typeof window === "undefined" ? "ask" : sectionFromHash(window.location.hash),
  );
  const [summary, setSummary] = useState<WorkbenchSummary | null>(null);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [wikiIndex, setWikiIndex] = useState<WikiIndexPayload | null>(null);
  const [selectedPageStem, setSelectedPageStem] = useState<string | null>(null);
  const [selectedPage, setSelectedPage] = useState<WikiPagePayload | null>(null);
  const [pageFilter, setPageFilter] = useState<PageFilterId>("all");
  const [pageError, setPageError] = useState<string | null>(null);
  const [selectedSourceStem, setSelectedSourceStem] = useState<string | null>(null);
  const [selectedSource, setSelectedSource] = useState<SourceDetailPayload | null>(null);
  const [sourceError, setSourceError] = useState<string | null>(null);
  const [reviewSummary, setReviewSummary] = useState<WorkbenchReviewPayload | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [warehouseSummary, setWarehouseSummary] = useState<WarehouseSummaryPayload | null>(null);
  const [warehouseError, setWarehouseError] = useState<string | null>(null);
  const [queryInput, setQueryInput] = useState("이 작업공간이 ontology builders에 대해 현재 무엇을 알고 있나?");
  const [queryResult, setQueryResult] = useState<QueryPreviewPayload | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [queryBusy, setQueryBusy] = useState(false);
  const [saveResult, setSaveResult] = useState<SaveAnalysisPayload | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveBusy, setSaveBusy] = useState(false);
  const [draftSummary, setDraftSummary] = useState<DraftSourceSummaryPayload | null>(null);
  const [draftSummaryError, setDraftSummaryError] = useState<string | null>(null);
  const [draftSummaryBusy, setDraftSummaryBusy] = useState(false);
  const [reviewActionResult, setReviewActionResult] = useState<ReviewClaimPayload | null>(null);
  const [reviewActionError, setReviewActionError] = useState<string | null>(null);
  const [reviewActionBusyId, setReviewActionBusyId] = useState<string | null>(null);
  const [doctorResult, setDoctorResult] = useState<WorkbenchActionPayload | null>(null);
  const [doctorError, setDoctorError] = useState<string | null>(null);
  const [doctorBusyAction, setDoctorBusyAction] = useState<WorkbenchActionKey | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const applyHash = () => setActiveSection(sectionFromHash(window.location.hash));
    window.addEventListener("hashchange", applyHash);
    return () => window.removeEventListener("hashchange", applyHash);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([fetchWorkbenchSummary(controller.signal), fetchWikiIndex(controller.signal)])
      .then(([summaryPayload, indexPayload]) => {
        setSummary(summaryPayload);
        setWikiIndex(indexPayload);
        setSummaryError(null);
      })
      .catch((error: Error) => {
        if (controller.signal.aborted) {
          return;
        }
        setSummary(null);
        setSummaryError(error.message);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!wikiIndex) {
      return;
    }
    const firstPage =
      wikiIndex.sections
        .filter((section) => section.name !== "Meta")
        .flatMap((section) => section.entries)[0] ?? null;
    if (!selectedPageStem && firstPage) {
      setSelectedPageStem(firstPage.stem);
    }
    const firstSource =
      wikiIndex.sections.find((section) => section.name === "Sources")?.entries[0] ?? null;
    if (!selectedSourceStem && firstSource) {
      setSelectedSourceStem(firstSource.stem);
    }
  }, [selectedPageStem, wikiIndex]);

  useEffect(() => {
    if (!selectedPageStem) {
      return;
    }
    const controller = new AbortController();
    fetchWikiPage(selectedPageStem, controller.signal)
      .then((payload) => {
        setSelectedPage(payload);
        setPageError(null);
      })
      .catch((error: Error) => {
        if (controller.signal.aborted) {
          return;
        }
        setSelectedPage(null);
        setPageError(error.message);
      });
    return () => controller.abort();
  }, [selectedPageStem]);

  useEffect(() => {
    const controller = new AbortController();
    fetchWorkbenchReview(8, controller.signal)
      .then((payload) => {
        setReviewSummary(payload);
        setReviewError(null);
      })
      .catch((error: Error) => {
        if (controller.signal.aborted) {
          return;
        }
        setReviewSummary(null);
        setReviewError(error.message);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchWarehouseSummary(controller.signal)
      .then((payload) => {
        setWarehouseSummary(payload);
        setWarehouseError(null);
      })
      .catch((error: Error) => {
        if (controller.signal.aborted) {
          return;
        }
        setWarehouseSummary(null);
        setWarehouseError(error.message);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!selectedSourceStem) {
      return;
    }
    const controller = new AbortController();
    fetchSourceDetail(selectedSourceStem, controller.signal)
      .then((payload) => {
        setSelectedSource(payload);
        setSourceError(null);
      })
      .catch((error: Error) => {
        if (controller.signal.aborted) {
          return;
        }
        setSelectedSource(null);
        setSourceError(error.message);
      });
    return () => controller.abort();
  }, [selectedSourceStem]);

  async function handleQueryPreview() {
    const nextQuestion = queryInput.trim();
    setQueryBusy(true);
    setQueryError(null);
    setSaveResult(null);
    setSaveError(null);
    try {
      const payload = await fetchQueryPreview(nextQuestion);
      setQueryResult(payload);
    } catch (error) {
      setQueryResult(null);
      setQueryError(error instanceof Error ? error.message : "질문 미리보기 중 알 수 없는 오류가 발생했습니다.");
    } finally {
      setQueryBusy(false);
    }
  }

  async function runSuggestedQuestion(question: string) {
    setQueryInput(question);
    setQueryBusy(true);
    setQueryError(null);
    setSaveResult(null);
    setSaveError(null);
    try {
      const payload = await fetchQueryPreview(question);
      setQueryResult(payload);
    } catch (error) {
      setQueryResult(null);
      setQueryError(error instanceof Error ? error.message : "질문 미리보기 중 알 수 없는 오류가 발생했습니다.");
    } finally {
      setQueryBusy(false);
    }
  }

  async function handleSaveAnalysis() {
    const nextQuestion = queryResult?.question.trim() || queryInput.trim();
    setSaveBusy(true);
    setSaveError(null);
    try {
      const payload = await saveAnalysis(nextQuestion);
      setSaveResult(payload);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "저장 중 알 수 없는 오류가 발생했습니다.");
    } finally {
      setSaveBusy(false);
    }
  }

  async function handleDraftSourceSummary() {
    if (!selectedSourceStem) {
      return;
    }
    setDraftSummaryBusy(true);
    setDraftSummaryError(null);
    try {
      const payload = await draftSourceSummary(selectedSourceStem);
      setDraftSummary(payload);
    } catch (error) {
      setDraftSummary(null);
      setDraftSummaryError(error instanceof Error ? error.message : "초안 생성 중 알 수 없는 오류가 발생했습니다.");
    } finally {
      setDraftSummaryBusy(false);
    }
  }

  async function handleReviewClaim(claimId: string, reviewState: "approved" | "rejected") {
    setReviewActionBusyId(claimId);
    setReviewActionError(null);
    try {
      const payload = await reviewClaim(claimId, reviewState);
      setReviewActionResult(payload);
      const refreshedReview = await fetchWorkbenchReview(8);
      setReviewSummary(refreshedReview);
      if (selectedSourceStem) {
        const refreshedSource = await fetchSourceDetail(selectedSourceStem);
        setSelectedSource(refreshedSource);
      }
    } catch (error) {
      setReviewActionResult(null);
      setReviewActionError(error instanceof Error ? error.message : "claim 검토 중 알 수 없는 오류가 발생했습니다.");
    } finally {
      setReviewActionBusyId(null);
    }
  }

  async function handleDoctorAction(action: WorkbenchActionKey) {
    setDoctorBusyAction(action);
    setDoctorError(null);
    try {
      const payload = await runWorkbenchAction(action);
      setDoctorResult(payload);
    } catch (error) {
      setDoctorResult(null);
      setDoctorError(error instanceof Error ? error.message : "Doctor action 실행 중 알 수 없는 오류가 발생했습니다.");
    } finally {
      setDoctorBusyAction(null);
    }
  }

  const pageSections = wikiIndex?.sections.filter((item) => item.name !== "Meta") ?? [];
  const filteredPageSections = pageSections.filter((group) => {
    if (pageFilter === "all") {
      return true;
    }
    return group.name.toLowerCase() === pageFilter;
  });
  const filteredPageCount = filteredPageSections.reduce((count, group) => count + group.entries.length, 0);
  const workspaceSectionCount = pageSections.length;
  const selectedPageHtml = renderMarkdown(selectedPage?.body ?? "# 페이지를 선택하세요");
  const queryResultHtml = renderMarkdown(
    queryResult?.answer_markdown ?? "# 질문\n\n질문을 입력하면 근거가 있는 초안을 여기에서 확인할 수 있습니다.",
  );
  const askHasSideContent = Boolean(queryResult?.related_pages.length || queryResult?.related_sources.length);
  const layoutClass =
    activeSection === "home"
      ? "simple-layout home-layout"
      : activeSection === "ask"
      ? askHasSideContent
        ? "simple-layout ask-layout ask-layout-with-side"
        : "simple-layout ask-layout"
      : activeSection === "sources" ||
          activeSection === "review" ||
          activeSection === "warehouse" ||
          activeSection === "doctor" ||
          activeSection === "graph"
        ? "simple-layout lane-layout"
      : "simple-layout wiki-layout";
  const section = sections.find((item) => item.id === activeSection) ?? sections[0];
  const SectionIcon = section.icon;
  const activeStatusLabel =
    activeSection === "ask"
      ? queryResult
        ? coverageLabel(queryResult.coverage)
        : "질문 준비됨"
      : `${filteredPageCount}개 표시 중`;

  const openWikiPage = (stem: string) => {
    startTransition(() => {
      setSelectedPageStem(stem);
      setActiveSection("wiki");
      window.location.hash = "wiki";
    });
  };

  const openSourcePage = (stem: string) => {
    startTransition(() => {
      setSelectedSourceStem(stem);
      setActiveSection("sources");
      window.location.hash = "sources";
    });
  };

  const primarySections = sections.filter((item) => item.rail === "primary");
  const advancedSections = sections.filter((item) => item.rail === "advanced");
  const graphSurface = buildGraphSurface(summary);

  return (
    <div className="app-shell simple-shell">
      <aside className="sidebar simple-sidebar">
        <div className="brand-block simple-brand">
          <div className="brand-logo-lockup">
            <img className="brand-logo-image" src="/doctology-logo.jpeg" alt="LLM Wiki workspace logo" />
          </div>
          <div className="brand-copy-block">
            <p className="eyebrow">LLM Wiki</p>
            <h1>LLM Wiki 작업공간</h1>
            <p className="brand-copy">근거 기반 질문과 문서 검토를 위한 repo-native 작업공간</p>
          </div>
        </div>

        <div className="workspace-stats">
          <div className="workspace-stat-card">
            <span>페이지</span>
            <strong>{summary ? summary.wiki.page_count : "—"}</strong>
          </div>
          <div className="workspace-stat-card">
            <span>섹션</span>
            <strong>{workspaceSectionCount || "—"}</strong>
          </div>
        </div>

        <nav className="nav-list" aria-label="주요 섹션">
          {primarySections.map((item) => {
            const Icon = item.icon;
            const active = item.id === activeSection;
            return (
              <button
                key={item.id}
                type="button"
                className={`nav-item ${active ? "nav-item-active" : ""}`}
                onClick={() => {
                  setActiveSection(item.id);
                  window.location.hash = item.id;
                }}
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="advanced-nav-block">
          <p className="eyebrow">Advanced</p>
          <nav className="nav-list" aria-label="고급 섹션">
            {advancedSections.map((item) => {
              const Icon = item.icon;
              const active = item.id === activeSection;
              return (
                <button
                  key={item.id}
                  type="button"
                  className={`nav-item ${active ? "nav-item-active" : ""}`}
                  onClick={() => {
                    setActiveSection(item.id);
                    window.location.hash = item.id;
                  }}
                >
                  <Icon size={16} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        <div className="connection-badge simple-badge">
          <span>{summaryError ? "어댑터 오프라인" : "어댑터 연결됨"}</span>
          <strong>{summary ? `인덱스 항목 ${summary.wiki.index_entry_count}개` : "어댑터 대기 중"}</strong>
        </div>
      </aside>

      <main className="main-stage simple-main">
        <header className="topbar simple-topbar">
          <div className="topbar-main">
            <div className="topbar-meta-row">
              <span className="meta-chip meta-chip-strong">{section.eyebrow}</span>
              {summary ? <span className="meta-chip">페이지 {summary.wiki.page_count}개</span> : null}
              <span className="meta-chip">{activeStatusLabel}</span>
            </div>
            <div className="topbar-heading-row">
              <div className="simple-title-row">
                <SectionIcon size={18} />
                <h2>{section.title}</h2>
              </div>
              <p className="topbar-copy">{section.description}</p>
            </div>
          </div>
        </header>

        <section className={layoutClass}>
          {activeSection === "home" ? (
            <div className="reader-panel simple-panel home-panel">
              <section className="home-hero">
                <p className="eyebrow">Beginner landing</p>
                <h3>작업을 먼저 고르고, 실제 레인으로 들어가세요</h3>
                <p className="home-copy">
                  이 작업공간은 위키에 있는 지식을 근거와 함께 확인하고, 소스별 검토와 draft-only 업데이트 preview를 안전하게 다루도록 설계됐습니다.
                </p>
              </section>

              <section className="home-card-grid">
                <button type="button" className="home-card" onClick={() => setActiveSection("ask")}>
                  <span>AI와 대화</span>
                  <strong>근거를 먼저 확인하는 질문 레인</strong>
                  <p>Ask로 이동해 coverage, warnings, provenance를 확인한 뒤 저장 가능한 분석만 남깁니다.</p>
                </button>
                <button type="button" className="home-card" onClick={() => setActiveSection("sources")}>
                  <span>위키 업데이트</span>
                  <strong>소스 검토와 draft-only 초안 레인</strong>
                  <p>Sources로 이동해 source detail, review queue, draft-only source summary preview를 확인합니다.</p>
                </button>
              </section>

              <section className="message-panel">
                <p className="eyebrow">Advanced rail</p>
                <ul className="compact-list compact-list-plain detail-list">
                  <li>운영 검토는 `검토` 섹션에서 low coverage, stale, low-confidence claim을 triage합니다.</li>
                  <li>고급 operator surface는 기본 홈이 아니라 필요한 경우에만 들어가는 secondary rail로 유지합니다.</li>
                </ul>
              </section>
            </div>
          ) : activeSection === "ask" ? (
            <>
              <div className="reader-panel simple-panel ask-main-panel">
                <div className="panel-header panel-header-compact">
                  <div>
                    <p className="eyebrow">근거 기반 질문</p>
                    <h3>한 번 묻고, 근거를 확인한 뒤, 남길 가치가 있는 답만 저장하세요</h3>
                  </div>
                  <span className="reader-status">{coverageLabel(queryResult?.coverage ?? "ready")}</span>
                </div>

                <div className="ask-top-grid">
                  <form
                    className="ask-form ask-form-card"
                    onSubmit={(event) => {
                      event.preventDefault();
                      void handleQueryPreview();
                    }}
                  >
                    <label className="field-label" htmlFor="ask-input">
                      질문
                    </label>
                    <textarea
                      id="ask-input"
                      className="ask-input"
                      value={queryInput}
                      onChange={(event) => setQueryInput(event.target.value)}
                      rows={4}
                    />
                    <p className="helper-copy">이름, 주제, 소스 종류, 시점을 구체적으로 적을수록 근거 있는 미리보기가 잘 나옵니다.</p>
                    <div className="future-surface-actions">
                      <button type="submit" className="doctor-button" disabled={queryBusy}>
                        {queryBusy ? "검색 중..." : "질문하기"}
                      </button>
                      <button
                        type="button"
                        className="doctor-button"
                        disabled={!queryResult || saveBusy}
                        onClick={() => void handleSaveAnalysis()}
                      >
                        {saveBusy ? "저장 중..." : "저장"}
                      </button>
                    </div>
                  </form>

                  <div className="ask-summary-card flow-card">
                    <p className="eyebrow">작업 흐름</p>
                    <h4>빠른 루프</h4>
                    <ul className="compact-list compact-list-plain workflow-list">
                      <li>
                        <strong>질문</strong>
                        <span>자유 대화처럼 시작하지 말고, 먼저 현재 위키에 있는 내용을 기준으로 묻습니다.</span>
                      </li>
                      <li>
                        <strong>검토</strong>
                        <span>근거 범위, 관련 페이지, 소스 목록을 보고 초안을 신뢰할지 판단합니다.</span>
                      </li>
                      <li>
                        <strong>저장</strong>
                        <span>장기적으로 남길 가치가 있는 답변만 분석 페이지로 저장합니다.</span>
                      </li>
                    </ul>
                  </div>
                </div>

                {queryResult ? (
                  <section className="ask-evidence-grid">
                    <article className="evidence-card">
                      <span>Coverage</span>
                      <strong>{coverageLabel(queryResult.coverage)}</strong>
                      <p>
                        {queryResult.coverage === "supported"
                          ? "위키 페이지와 소스 또는 canonical registry가 함께 맞물립니다."
                          : queryResult.coverage === "thin"
                            ? "일부 근거는 있지만, 저장 전 검토가 필요합니다."
                            : "질문을 더 구체화해야 신뢰할 만한 초안이 나옵니다."}
                      </p>
                    </article>
                    <article className="evidence-card">
                      <span>근거 묶음</span>
                      <strong>{queryResult.provenance_sections.reduce((sum, section) => sum + section.count, 0)}</strong>
                      <p>위키, 소스, canonical registry에서 끌어온 근거 묶음 수입니다.</p>
                    </article>
                    <article className="evidence-card">
                      <span>저장 준비</span>
                      <strong>{queryResult.coverage === "none" ? "재질문 필요" : "검토 후 저장 가능"}</strong>
                      <p>채팅처럼 넘기지 말고, 근거를 확인한 뒤 남길 가치가 있는 답만 저장하세요.</p>
                    </article>
                  </section>
                ) : null}

                {queryResult?.warnings.length ? (
                  <section className="message-panel warning-panel">
                    <p className="eyebrow">Warnings</p>
                    <ul className="compact-list compact-list-plain detail-list">
                      {queryResult.warnings.map((warning) => (
                        <li key={warning}>{warningLabel(warning)}</li>
                      ))}
                    </ul>
                  </section>
                ) : null}

                {queryResult?.provenance_sections.length ? (
                  <section className="message-panel provenance-panel">
                    <p className="eyebrow">Provenance</p>
                    <div className="provenance-grid">
                      {queryResult.provenance_sections.map((section) => (
                        <article key={section.label} className="provenance-card">
                          <span>{section.label}</span>
                          <strong>{section.count}</strong>
                          <p>{section.count > 0 ? "이 묶음에서 근거를 확인했습니다." : "현재는 직접 근거가 없습니다."}</p>
                        </article>
                      ))}
                    </div>
                  </section>
                ) : null}

                {queryError ? <p className="error-copy">{queryError}</p> : null}
                {saveError ? <p className="error-copy">{saveError}</p> : null}
                {saveResult ? (
                  <SaveResultPanel saveResult={saveResult} onOpenAnalysis={openWikiPage} />
                ) : null}

                {queryResult ? (
                  <article className="markdown-surface wiki-surface" dangerouslySetInnerHTML={{ __html: queryResultHtml }} />
                ) : (
                  <section className="markdown-surface wiki-surface empty-state-surface">
                    <p className="eyebrow">시작 질문</p>
                    <h3>구체적으로 물어보면 저장소가 근거와 함께 보여줍니다</h3>
                    <p className="empty-state-copy">
                      인물, 개념, 소스 계열, 저장소 질문처럼 범위가 분명한 질문이 좋습니다. 근거가 약하면 미리보기에서 그대로 드러납니다.
                    </p>
                    <div className="suggestion-list">
                      {starterQuestions.map((question) => (
                        <button
                          key={question}
                          type="button"
                          className="suggestion-card"
                          onClick={() => void runSuggestedQuestion(question)}
                          disabled={queryBusy}
                        >
                          <strong>{question}</strong>
                          <span>이 질문 실행</span>
                        </button>
                      ))}
                    </div>
                  </section>
                )}
              </div>

              {askHasSideContent ? (
                <div className="inspector-panel simple-panel ask-side-panel">
                  <RelatedPageList title="관련 페이지" pages={queryResult?.related_pages ?? []} onOpen={openWikiPage} />
                  <RelatedPageList title="소스 페이지" pages={queryResult?.related_sources ?? []} onOpen={openWikiPage} />
                </div>
              ) : null}
            </>
          ) : activeSection === "wiki" ? (
            <>
              <div className="inspector-panel simple-panel wiki-index-panel">
                <div className="panel-header panel-header-compact panel-header-stack">
                  <div>
                    <p className="eyebrow">탐색</p>
                    <h3>위키 페이지</h3>
                  </div>
                  <p className="panel-copy">제목 중심 목록과 필터를 이용해 볼트 안의 페이지를 빠르게 이동합니다.</p>
                </div>

                <div className="selection-list simple-selection-list">
                  <div className="filter-chip-row">
                    {(["all", "sources", "analyses", "concepts", "entities", "people", "projects", "timelines"] as PageFilterId[]).map(
                      (item) => (
                        <button
                          key={item}
                          type="button"
                          className={`filter-chip ${pageFilter === item ? "filter-chip-active" : ""}`}
                          onClick={() => setPageFilter(item)}
                        >
                          {pageFilterLabel(item)}
                        </button>
                      ),
                    )}
                  </div>
                  {filteredPageSections.map((group) => (
                    <section key={group.name} className="selection-group">
                      <h4>
                        {sectionNameLabel(group.name)}
                        <span>{group.entries.length}</span>
                      </h4>
                      {group.entries.map((entry) => {
                        const title = entry.title ?? entry.stem;
                        return (
                          <button
                            key={entry.stem}
                            type="button"
                            className={`selection-item ${selectedPageStem === entry.stem ? "selection-item-active" : ""}`}
                            onClick={() =>
                              startTransition(() => {
                                setSelectedPageStem(entry.stem);
                              })
                            }
                          >
                            <strong className="selection-title">{title}</strong>
                            <span className="selection-meta">{entry.stem}</span>
                            <span className="selection-summary">{entry.summary}</span>
                          </button>
                        );
                      })}
                    </section>
                  ))}
                  <RelatedPageList title="관련 페이지" pages={selectedPage?.related_pages ?? []} onOpen={openWikiPage} />
                </div>
              </div>

              <div className="reader-panel simple-panel wiki-reader-panel">
                <div className="panel-header panel-header-compact">
                  <div>
                    <p className="eyebrow">문서</p>
                    <h3>{selectedPage?.frontmatter.title?.toString() ?? "페이지를 선택하세요"}</h3>
                  </div>
                  <span className="reader-status">{sectionNameLabel(selectedPage?.section ?? "wiki")}</span>
                </div>
                {pageError ? <p className="error-copy">{pageError}</p> : null}
                <article className="markdown-surface wiki-surface" dangerouslySetInnerHTML={{ __html: selectedPageHtml }} />
              </div>
            </>
          ) : activeSection === "sources" ? (
            <>
              <div className="inspector-panel simple-panel lane-list-panel">
                <div className="panel-header panel-header-compact panel-header-stack">
                  <div>
                    <p className="eyebrow">소스 목록</p>
                    <h3>소스 페이지</h3>
                  </div>
                  <p className="panel-copy">source detail, coverage, review queue, draft-only 초안 생성을 한 레인에서 다룹니다.</p>
                </div>
                <div className="selection-list simple-selection-list">
                  {(pageSections.find((group) => group.name === "Sources")?.entries ?? []).map((entry) => (
                    <button
                      key={entry.stem}
                      type="button"
                      className={`selection-item ${selectedSourceStem === entry.stem ? "selection-item-active" : ""}`}
                      onClick={() => setSelectedSourceStem(entry.stem)}
                    >
                      <strong className="selection-title">{entry.title ?? entry.stem}</strong>
                      <span className="selection-meta">{entry.stem}</span>
                      <span className="selection-summary">{entry.summary}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="reader-panel simple-panel lane-reader-panel">
                <div className="panel-header panel-header-compact">
                  <div>
                    <p className="eyebrow">소스 상세</p>
                    <h3>{selectedSource?.frontmatter.title?.toString() ?? "소스를 선택하세요"}</h3>
                  </div>
                  <span className="reader-status">Update lane</span>
                </div>
                {sourceError ? <p className="error-copy">{sourceError}</p> : null}
                {draftSummaryError ? <p className="error-copy">{draftSummaryError}</p> : null}
                {reviewActionError ? <p className="error-copy">{reviewActionError}</p> : null}
                {reviewActionResult ? (
                  <section className="message-panel">
                    <p className="eyebrow">Claim updated</p>
                    <ul className="compact-list compact-list-plain detail-list">
                      <li>{reviewActionResult.claim_id}</li>
                      <li>{reviewActionResult.review_state}</li>
                      <li>{reviewActionResult.changed_files.join(", ")}</li>
                    </ul>
                  </section>
                ) : null}
                {selectedSource ? (
                  <>
                    <section className="ask-evidence-grid">
                      <article className="evidence-card">
                        <span>Raw path</span>
                        <strong>{selectedSource.raw_path ?? "없음"}</strong>
                        <p>원본 source 파일 또는 note 경로입니다.</p>
                      </article>
                      <article className="evidence-card">
                        <span>Claim coverage</span>
                        <strong>{selectedSource.coverage.claim_count}</strong>
                        <p>
                          approved {selectedSource.coverage.approved_claim_count} / pending {selectedSource.coverage.pending_claim_count}
                        </p>
                      </article>
                      <article className="evidence-card">
                        <span>Incremental status</span>
                        <strong>{selectedSource.incremental_status?.latest_export_version_id ?? "없음"}</strong>
                        <p>latest export version 또는 incremental status page 기준 상태입니다.</p>
                      </article>
                    </section>

                    <section className="message-panel">
                      <div className="save-result-header">
                        <div>
                          <p className="eyebrow">Draft-only update preview</p>
                          <h4>소스 요약 초안</h4>
                        </div>
                        <button type="button" className="ghost-button" onClick={() => void handleDraftSourceSummary()} disabled={draftSummaryBusy}>
                          {draftSummaryBusy ? "초안 생성 중..." : "초안 만들기"}
                        </button>
                      </div>
                      <p className="panel-copy">이 액션은 backend-gated draft만 반환하며 `raw/`나 canonical truth를 직접 수정하지 않습니다.</p>
                      {draftSummary ? (
                        <article className="markdown-surface" dangerouslySetInnerHTML={{ __html: renderMarkdown(draftSummary.draft_markdown) }} />
                      ) : null}
                    </section>

                    <section className="message-panel">
                      <p className="eyebrow">Review queue</p>
                      <ul className="compact-list compact-list-plain detail-list">
                        {selectedSource.review_queue.length ? (
                          selectedSource.review_queue.map((item) => (
                            <li key={item.claim_id} className="review-item">
                              <div>
                                <strong>{item.claim_id}</strong>
                                <p>{item.claim_text ?? item.predicate ?? "claim text 없음"}</p>
                              </div>
                              <div className="review-actions">
                                <button
                                  type="button"
                                  className="ghost-button"
                                  disabled={reviewActionBusyId === item.claim_id}
                                  onClick={() => void handleReviewClaim(item.claim_id, "approved")}
                                >
                                  승인
                                </button>
                                <button
                                  type="button"
                                  className="ghost-button"
                                  disabled={reviewActionBusyId === item.claim_id}
                                  onClick={() => void handleReviewClaim(item.claim_id, "rejected")}
                                >
                                  거절
                                </button>
                              </div>
                            </li>
                          ))
                        ) : (
                          <li>현재 source-local review queue는 비어 있습니다.</li>
                        )}
                      </ul>
                    </section>
                  </>
                ) : null}
              </div>
            </>
          ) : activeSection === "review" ? (
            <>
              <div className="inspector-panel simple-panel lane-list-panel">
                <div className="panel-header panel-header-compact panel-header-stack">
                  <div>
                    <p className="eyebrow">검토 큐</p>
                    <h3>운영 검토 레인</h3>
                  </div>
                  <p className="panel-copy">low coverage, stale, uncertainty, low-confidence claim을 한 곳에서 triage합니다.</p>
                </div>
                {reviewError ? <p className="error-copy">{reviewError}</p> : null}
                {reviewSummary ? (
                  <div className="selection-list simple-selection-list">
                    <section className="selection-group">
                      <h4>Low coverage <span>{reviewSummary.low_coverage_pages.length}</span></h4>
                      {reviewSummary.low_coverage_pages.map((item) => (
                        <button key={item.stem} type="button" className="selection-item" onClick={() => openWikiPage(item.stem)}>
                          <strong className="selection-title">{item.title}</strong>
                          <span className="selection-summary">{item.reason ?? item.section}</span>
                        </button>
                      ))}
                    </section>
                    <section className="selection-group">
                      <h4>Stale <span>{reviewSummary.stale_pages.length}</span></h4>
                      {reviewSummary.stale_pages.map((item) => (
                        <button key={item.stem} type="button" className="selection-item" onClick={() => openWikiPage(item.stem)}>
                          <strong className="selection-title">{item.title}</strong>
                          <span className="selection-summary">{item.age_days ?? "?"}일 경과</span>
                        </button>
                      ))}
                    </section>
                    <section className="selection-group">
                      <h4>Uncertainty <span>{reviewSummary.uncertainty_candidates.length}</span></h4>
                      {reviewSummary.uncertainty_candidates.map((item) => (
                        <button key={item.stem} type="button" className="selection-item" onClick={() => openWikiPage(item.stem)}>
                          <strong className="selection-title">{item.title}</strong>
                          <span className="selection-summary">{item.reason ?? item.section}</span>
                        </button>
                      ))}
                    </section>
                  </div>
                ) : null}
              </div>

              <div className="reader-panel simple-panel lane-reader-panel">
                <div className="panel-header panel-header-compact">
                  <div>
                    <p className="eyebrow">Low-confidence claims</p>
                    <h3>Canonical claim triage</h3>
                  </div>
                  <span className="reader-status">Canonical only</span>
                </div>
                {reviewSummary ? (
                  <ul className="compact-list compact-list-plain detail-list">
                    {reviewSummary.low_confidence_claims.length ? (
                      reviewSummary.low_confidence_claims.map((item) => (
                        <li key={item.claim_id} className="review-item">
                          <div>
                            <strong>{item.claim_id}</strong>
                            <p>{item.claim_text ?? "claim text 없음"}</p>
                            <p>source page: {item.source_page ?? "없음"} / confidence: {item.confidence ?? "?"}</p>
                          </div>
                          <div className="review-actions">
                            {item.source_page ? (
                              <button type="button" className="ghost-button" onClick={() => openSourcePage(item.source_page!)}>
                                소스 열기
                              </button>
                            ) : null}
                            <button
                              type="button"
                              className="ghost-button"
                              disabled={reviewActionBusyId === item.claim_id}
                              onClick={() => void handleReviewClaim(item.claim_id, "approved")}
                            >
                              승인
                            </button>
                            <button
                              type="button"
                              className="ghost-button"
                              disabled={reviewActionBusyId === item.claim_id}
                              onClick={() => void handleReviewClaim(item.claim_id, "rejected")}
                            >
                              거절
                            </button>
                          </div>
                        </li>
                      ))
                    ) : (
                      <li>현재 low-confidence claim queue는 비어 있습니다.</li>
                    )}
                  </ul>
                ) : null}
              </div>
            </>
          ) : activeSection === "warehouse" ? (
            <>
              <div className="inspector-panel simple-panel lane-list-panel">
                <div className="panel-header panel-header-compact panel-header-stack">
                  <div>
                    <p className="eyebrow">Canonical registries</p>
                    <h3>Warehouse 목록</h3>
                  </div>
                  <p className="panel-copy">registry count와 truth class를 읽기 전용으로 확인합니다.</p>
                </div>
                {warehouseError ? <p className="error-copy">{warehouseError}</p> : null}
                {warehouseSummary ? (
                  <div className="selection-list simple-selection-list">
                    {warehouseSummary.registries.map((registry) => (
                      <article key={registry.key} className="selection-item">
                        <strong className="selection-title">{registry.key}</strong>
                        <span className="selection-meta">{registry.truth_class}</span>
                        <span className="selection-summary">{registry.count} rows</span>
                      </article>
                    ))}
                  </div>
                ) : null}
              </div>

              <div className="reader-panel simple-panel lane-reader-panel">
                <div className="panel-header panel-header-compact">
                  <div>
                    <p className="eyebrow">Read-only inspection</p>
                    <h3>Registry sample preview</h3>
                  </div>
                  <span className="reader-status">Read only</span>
                </div>
                {warehouseSummary ? (
                  <div className="selection-list simple-selection-list">
                    {warehouseSummary.registries.map((registry) => (
                      <section key={registry.key} className="message-panel">
                        <p className="eyebrow">{registry.key}</p>
                        <ul className="compact-list compact-list-plain detail-list">
                          <li>truth class: {registry.truth_class}</li>
                          <li>path: {registry.path}</li>
                          <li>count: {registry.count}</li>
                        </ul>
                      </section>
                    ))}
                  </div>
                ) : null}
              </div>
            </>
          ) : activeSection === "doctor" ? (
            <>
              <div className="inspector-panel simple-panel lane-list-panel">
                <div className="panel-header panel-header-compact panel-header-stack">
                  <div>
                    <p className="eyebrow">Doctor actions</p>
                    <h3>명시적 실행</h3>
                  </div>
                  <p className="panel-copy">status, reindex, lint만 실행하고 구조화된 결과를 확인합니다.</p>
                </div>
                <div className="future-surface-actions">
                  {(["status", "reindex", "lint"] as WorkbenchActionKey[]).map((action) => (
                    <button
                      key={action}
                      type="button"
                      className="doctor-button"
                      disabled={doctorBusyAction !== null}
                      onClick={() => void handleDoctorAction(action)}
                    >
                      {doctorBusyAction === action ? `${action} 실행 중...` : action}
                    </button>
                  ))}
                </div>
                {doctorError ? <p className="error-copy">{doctorError}</p> : null}
              </div>

              <div className="reader-panel simple-panel lane-reader-panel">
                <div className="panel-header panel-header-compact">
                  <div>
                    <p className="eyebrow">Action result</p>
                    <h3>{doctorResult?.action ?? "실행 결과를 기다리는 중"}</h3>
                  </div>
                  <span className="reader-status">Audited</span>
                </div>
                {doctorResult ? (
                  <section className="message-panel">
                    <ul className="compact-list compact-list-plain detail-list">
                      <li>command: {doctorResult.command}</li>
                      <li>exit code: {doctorResult.exit_code}</li>
                    </ul>
                    <div className="selection-list simple-selection-list">
                      {doctorResult.stdout_lines.length ? (
                        <article className="selection-item">
                          <strong className="selection-title">stdout</strong>
                          <span className="selection-summary">{doctorResult.stdout_lines.join(" | ")}</span>
                        </article>
                      ) : null}
                      {doctorResult.stderr_lines.length ? (
                        <article className="selection-item">
                          <strong className="selection-title">stderr</strong>
                          <span className="selection-summary">{doctorResult.stderr_lines.join(" | ")}</span>
                        </article>
                      ) : null}
                    </div>
                  </section>
                ) : null}
              </div>
            </>
          ) : activeSection === "graph" ? (
            <>
              <div className="inspector-panel simple-panel lane-list-panel">
                <div className="panel-header panel-header-compact panel-header-stack">
                  <div>
                    <p className="eyebrow">Graph contract</p>
                    <h3>{graphSurface.title}</h3>
                  </div>
                  <p className="panel-copy">{graphSurface.description}</p>
                </div>
                <section className="message-panel">
                  <p className="eyebrow">Boundaries</p>
                  <ul className="compact-list compact-list-plain detail-list">
                    <li>mode: {graphSurface.mode}</li>
                    <li>source path: {graphSurface.sourcePath}</li>
                    <li>seed node required before any render</li>
                    <li>default scope: bounded 1-hop inspect</li>
                  </ul>
                </section>
              </div>

              <div className="reader-panel simple-panel lane-reader-panel">
                <div className="panel-header panel-header-compact">
                  <div>
                    <p className="eyebrow">Derived only</p>
                    <h3>Graph notes</h3>
                  </div>
                  <span className="reader-status">Bounded</span>
                </div>
                <section className="message-panel">
                  <ul className="compact-list compact-list-plain detail-list">
                    {graphSurface.notes.map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                    <li>Graph는 canonical wiki와 registry truth보다 아래에 있는 보조 inspect surface입니다.</li>
                  </ul>
                </section>
              </div>
            </>
          ) : (
            <></>
          )}
        </section>
      </main>
    </div>
  );
}
