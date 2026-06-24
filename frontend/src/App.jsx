import { useState } from "react";
import axios from "axios";
import eyLogo from "./assets/ey-logo.png";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const [domaine, setDomaine] = useState("");
  const [bailleur, setBailleur] = useState("");
  const [pays, setPays] = useState("");
  const [region, setRegion] = useState("");
  const [useAgent, setUseAgent] = useState(false);

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [agentAnswer, setAgentAnswer] = useState("");
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  const scrollToSearch = (e) => {
    e.preventDefault();
    document.getElementById("search").scrollIntoView({ behavior: "smooth" });
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError("");
    setAgentAnswer("");
    setResults([]);
    setHasSearched(true);

    const endpoint = useAgent ? "/api/agent-search" : "/api/search";

    try {
      const response = await axios.get(endpoint, {
        params: {
          query,
          domaine: domaine || undefined,
          bailleur: bailleur || undefined,
          pays: pays || undefined,
          region: region || undefined,
        },
      });

      if (useAgent) {
        setAgentAnswer(response.data.answer);
        setResults(response.data.sources || []);
      } else {
        setResults(response.data.results || []);
      }
    } catch (err) {
      setError(
        "La recherche n'a pas pu être effectuée. Vérifiez que le service est actif."
      );
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const scorePercent = (score) => Math.round(Math.min(score, 1) * 100);

  return (
    <div className="app">
      {/* TOPBAR */}
      <header className="topbar">
        <div className="brand">
          <img src={eyLogo} alt="EY" className="brand-logo" />
          <span className="brand-text">
            TENDERSCOPE
            <span className="brand-sub">Intelligence documentaire pour appels d'offres</span>
          </span>
        </div>
        <nav className="topnav">
          <a href="#search" onClick={scrollToSearch}>Recherche</a>
          <a href="#about" onClick={(e) => e.preventDefault()}>Méthodologie</a>
        </nav>
      </header>

      {/* HERO */}
      <section className="hero">
        <div className="hero-inner">
          <p className="hero-eyebrow">Plateforme Agentic RAG</p>
          <h1 className="hero-title">
            Chaque Terme de Référence,<br />interrogé en quelques secondes.
          </h1>
          <p className="hero-lede">
            Retrouvez instantanément les missions, profils et compétences exigées
            à travers l'ensemble de votre base documentaire d'appels d'offres.
          </p>

          <div className="hero-stats">
            <div className="stat">
              <span className="stat-number">98</span>
              <span className="stat-label">TdR indexés</span>
            </div>
            <div className="stat-divider" />
            <div className="stat">
              <span className="stat-number">3</span>
              <span className="stat-label">Langues couvertes</span>
            </div>
            <div className="stat-divider" />
            <div className="stat">
              <span className="stat-number">&lt;30s</span>
              <span className="stat-label">Par recherche enrichie</span>
            </div>
          </div>

          <button className="hero-cta" onClick={scrollToSearch}>
            Lancer une recherche
            <span className="hero-cta-arrow">↓</span>
          </button>
        </div>
      </section>

      {/* SEARCH */}
      <main className="content" id="search">
        <form className="search-panel" onSubmit={handleSearch}>
          <label className="panel-label">Rechercher une mission ou un profil</label>
          <div className="search-row">
            <input
              type="text"
              placeholder="Ex. profil vétérinaire Afrique de l'Ouest, expert M&E santé publique…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="search-input"
            />
            <button type="submit" className="search-button" disabled={loading}>
              {loading ? "Recherche en cours" : "Rechercher"}
            </button>
          </div>

          <div className="filters-row">
            <div className="filter-field">
              <label htmlFor="domaine">Domaine</label>
              <input id="domaine" type="text" placeholder="Ex. Santé animale" value={domaine} onChange={(e) => setDomaine(e.target.value)} />
            </div>
            <div className="filter-field">
              <label htmlFor="bailleur">Bailleur de fonds</label>
              <input id="bailleur" type="text" placeholder="Ex. AFD, UE, DGD" value={bailleur} onChange={(e) => setBailleur(e.target.value)} />
            </div>
            <div className="filter-field">
              <label htmlFor="pays">Pays</label>
              <input id="pays" type="text" placeholder="Ex. Burkina Faso" value={pays} onChange={(e) => setPays(e.target.value)} />
            </div>
            <div className="filter-field">
              <label htmlFor="region">Région</label>
              <input id="region" type="text" placeholder="Ex. Afrique de l'Ouest" value={region} onChange={(e) => setRegion(e.target.value)} />
            </div>
          </div>

          <label className="agent-toggle">
            <input
              type="checkbox"
              checked={useAgent}
              onChange={(e) => setUseAgent(e.target.checked)}
            />
            <span>
              Activer la synthèse par agent — reformule la requête et rédige une réponse argumentée
            </span>
          </label>
        </form>

        {error && <div className="error-box">{error}</div>}

        {agentAnswer && (
          <div className="agent-answer">
            <span className="agent-answer-eyebrow">Synthèse de l'agent</span>
            <p>{agentAnswer}</p>
          </div>
        )}

        {results.length > 0 && (
          <div className="results-list">
            <div className="results-header">
              <h2>{results.length} extrait{results.length > 1 ? "s" : ""} pertinent{results.length > 1 ? "s" : ""}</h2>
              <span className="results-sub">classés par pertinence sémantique</span>
            </div>

            {results.map((r, idx) => (
              <article className="result-card" key={idx}>
                <div className="result-score-block">
                  <div className="score-ring">
                    <span className="score-value">{scorePercent(r.score)}</span>
                    <span className="score-unit">%</span>
                  </div>
                  <span className="score-raw">score {r.score.toFixed(4)}</span>
                </div>
                <div className="result-body">
                  <div className="result-header">
                    <h3 className="result-file">{r.file}</h3>
                    {r.section && r.section !== "document" && (
                      <span className="result-section">{r.section}</span>
                    )}
                  </div>
                  <p className="result-text">{r.text?.slice(0, 600)}…</p>
                </div>
              </article>
            ))}
          </div>
        )}

        {!loading && hasSearched && results.length === 0 && !error && !agentAnswer && (
          <div className="empty-state">
            <p className="empty-title">Aucun résultat pour cette recherche.</p>
            <p>Essayez des termes plus généraux ou retirez certains filtres.</p>
          </div>
        )}

        {!hasSearched && (
          <div className="empty-state">
            <p className="empty-title">Prêt à interroger votre base de TdR.</p>
            <p>Lancez une recherche ci-dessus pour afficher les missions correspondantes.</p>
          </div>
        )}
      </main>

      <footer className="footer">
        <span>TENDERSCOPE — Agentic RAG pour appels d'offres internationaux</span>
      </footer>
    </div>
  );
}

export default App;