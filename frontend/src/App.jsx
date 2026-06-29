import { useState } from "react";
import axios from "axios";
import eyLogo from "./assets/ey-logo.png";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState({ domaine: "", bailleur: "", pays: "", region: "" });
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [agentAnswer, setAgentAnswer] = useState("");
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [similarMissions, setSimilarMissions] = useState({});
  const [loadingSimilar, setLoadingSimilar] = useState(null);
  const [expandedSimilar, setExpandedSimilar] = useState(null);

  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  const domaines = ["Santé", "Agriculture", "Développement", "Énergie", "Technologie", "Environnement"];
  const bailleurs = ["Banque Mondiale", "FMI", "PNUD", "Union Européenne", "AFD", "FIDA"];
  const pays = ["Sénégal", "Mali", "Burkina Faso", "Côte d'Ivoire", "Niger", "Autres"];
  const regions = ["Afrique de l'Ouest", "Afrique de l'Est", "Afrique Centrale", "Afrique Australe"];

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError("");
    setAgentAnswer("");
    setResults([]);
    setHasSearched(true);
    setSimilarMissions({});
    setExpandedSimilar(null);

    try {
      const body = {
        query: query,
        top_k: 5,
        score_threshold: 0.55,
        ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v)),
      };
      const response = await axios.post(API_URL + "/ask", body);
      setAgentAnswer(response.data.answer || "");
      setResults(response.data.sources || []);
    } catch (err) {
      console.error(err);
      setError("La recherche n'a pas pu être effectuée. Vérifiez que l'API FastAPI est démarrée.");
    } finally {
      setLoading(false);
    }
  };

  const fetchSimilar = async (fileName, idx) => {
    if (similarMissions[idx]) {
      setExpandedSimilar(expandedSimilar === idx ? null : idx);
      return;
    }
    setLoadingSimilar(idx);
    try {
      const response = await axios.post(API_URL + "/similar", { file_name: fileName, chunk_id: 0, top_k: 4 });
      setSimilarMissions((prev) => ({ ...prev, [idx]: response.data.results || [] }));
      setExpandedSimilar(idx);
    } catch (err) {
      console.error(err);
      setSimilarMissions((prev) => ({ ...prev, [idx]: [] }));
      setExpandedSimilar(idx);
    } finally {
      setLoadingSimilar(null);
    }
  };

  const resetFilters = () => {
    setFilters({ domaine: "", bailleur: "", pays: "", region: "" });
  };

  const scorePercent = (score) => Math.round(Math.min(score, 1) * 100);

  const scrollToSearch = (e) => {
    e.preventDefault();
    document.getElementById("search-section").scrollIntoView({ behavior: "smooth" });
  };

  const getDownloadUrl = (fileName) => API_URL + "/download/" + encodeURIComponent(fileName);

  const getScoreLabel = (score) => {
    const pct = scorePercent(score);
    if (pct >= 80) return "Très pertinent";
    if (pct >= 60) return "Pertinent";
    return "Possible";
  };

  const getSimilarButtonLabel = (idx) => {
    if (loadingSimilar === idx) return "Chargement…";
    if (expandedSimilar === idx) return "Masquer les missions similaires";
    return "Voir les missions similaires";
  };

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <img src={eyLogo} alt="EY" className="brand-logo" />
          <div className="brand-content">
            <span className="brand-text">TenderScope</span>
            <span className="brand-sub">Recherche intelligente de Termes de Référence</span>
          </div>
        </div>
        <nav className="topnav">
          <button onClick={scrollToSearch} className="nav-link">Recherche</button>
          <a href="#" className="nav-link">À propos</a>
        </nav>
      </header>

      <section className="hero">
        <div className="hero-content">
         <h1 className="hero-title">Le TdR pertinent, retrouvé par le sens <br />pas par hasard.</h1>          <p className="hero-description">Décrivez la mission en langage naturel. L'agent identifie le Terme de Référence pertinent et répond à partir de son contenu réel.</p>
          <button className="hero-cta" onClick={scrollToSearch}>Commencer la recherche</button>
        </div>
      </section>

      <section className="search-section" id="search-section">
        <div className="search-container">
          <h2 className="section-title">Recherche</h2>

          <form className="search-form" onSubmit={handleSearch}>
            <div className="search-input-group">
              <label className="search-label">Question</label>
              <div className="search-input-wrapper">
                <input type="text" placeholder="Ex: barème de notation des candidats ERP UVT" value={query} onChange={(e) => setQuery(e.target.value)} className="search-input" autoFocus />
                <button type="submit" className="search-btn" disabled={loading}>{loading ? "Analyse en cours…" : "Répondre"}</button>
              </div>
            </div>

            <div className="filters-section">
              <label className="filters-label">Filtres (optionnels)</label>
              <div className="filters-grid">
                <div className="filter-group">
                  <label htmlFor="domaine">Domaine</label>
                  <select id="domaine" value={filters.domaine} onChange={(e) => handleFilterChange("domaine", e.target.value)} className="filter-select">
                    <option value="">Tous les domaines</option>
                    {domaines.map((d) => <option key={d} value={d}>{d}</option>)}
                  </select>
                </div>
                <div className="filter-group">
                  <label htmlFor="bailleur">Bailleur de fonds</label>
                  <select id="bailleur" value={filters.bailleur} onChange={(e) => handleFilterChange("bailleur", e.target.value)} className="filter-select">
                    <option value="">Tous les bailleurs</option>
                    {bailleurs.map((b) => <option key={b} value={b}>{b}</option>)}
                  </select>
                </div>
                <div className="filter-group">
                  <label htmlFor="pays">Pays</label>
                  <select id="pays" value={filters.pays} onChange={(e) => handleFilterChange("pays", e.target.value)} className="filter-select">
                    <option value="">Tous les pays</option>
                    {pays.map((p) => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
                <div className="filter-group">
                  <label htmlFor="region">Région</label>
                  <select id="region" value={filters.region} onChange={(e) => handleFilterChange("region", e.target.value)} className="filter-select">
                    <option value="">Toutes les régions</option>
                    {regions.map((r) => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>
              </div>
              {Object.values(filters).some((v) => v) && (
                <button type="button" className="reset-filters-btn" onClick={resetFilters}>Réinitialiser les filtres</button>
              )}
            </div>
          </form>

          {loading && <div className="loading-hint">Analyse du document en cours — cela peut prendre jusqu'à 30 secondes.</div>}

          {error && (
            <div className="error-box">
              <span className="error-icon">⚠</span>
              <div><strong>Erreur</strong><p>{error}</p></div>
            </div>
          )}

          {hasSearched && !loading && (
            <div className="results-section">
              {results.length > 1 && (
                <div className="results-count-header">
                  <h3>{results.length} appels d'offres pertinents trouvés</h3>
                  <span>classés par pertinence sémantique</span>
                </div>
              )}

              {results.length === 0 ? (
                <div className="no-results"><p>Aucun TdR ne correspond à votre recherche.</p></div>
              ) : (
                results.map((result, idx) => (
                  <article className="doc-card" key={idx}>
                    <div className="doc-card-header">
                      <div className="doc-card-title-block">
                        <h3 className="doc-card-title">{result.file.replace(/\.pdf$/i, "")}</h3>
                        <div className="doc-card-meta">
                          {result.bailleur && <span><strong>Bailleur:</strong> {result.bailleur}</span>}
                          {result.pays && <span><strong>Pays:</strong> {result.pays}</span>}
                          {result.domaine && <span><strong>Domaine:</strong> {result.domaine}</span>}
                        </div>
                      </div>
                      <div className="doc-card-score">
                        <span className="doc-score-value">{scorePercent(result.score)}%</span>
                        <span className="doc-score-label">{getScoreLabel(result.score)}</span>
                      </div>
                    </div>

                    {idx === 0 && agentAnswer && (
                      <div className="doc-answer-box">
                        <span className="doc-answer-label">{results.length === 1 ? "Réponse d'après ce TdR" : "Synthèse basée sur les TdR les plus pertinents"}</span>
                        <p>{agentAnswer}</p>
                      </div>
                    )}

                    <div className="doc-card-actions">
                      <a href={getDownloadUrl(result.file)} className="doc-download-link" target="_blank" rel="noopener noreferrer">Télécharger le TdR</a>
                      <button className="doc-similar-toggle" onClick={() => fetchSimilar(result.file, idx)}>{getSimilarButtonLabel(idx)}</button>
                    </div>

                    {expandedSimilar === idx && (
                      <div className="similar-missions">
                        {similarMissions[idx]?.length > 0 ? (
                          <ul className="similar-list">
                            {similarMissions[idx].map((sim, simIdx) => (
                              <li key={simIdx} className="similar-item">
                                <span className="similar-file">{sim.file.replace(/\.pdf$/i, "")}</span>
                                <span className="similar-score">{scorePercent(sim.score)}%</span>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="similar-empty">Aucune mission similaire trouvée.</p>
                        )}
                      </div>
                    )}
                  </article>
                ))
              )}
            </div>
          )}
        </div>
      </section>

      <footer className="footer">
        <div className="footer-content">
          <p>&copy; 2024 TenderScope — Plateforme Agentic RAG pour Termes de Référence</p>
          <p className="footer-link">Développé en partenariat avec EY</p>
        </div>
      </footer>
    </div>
  );
}

export default App;