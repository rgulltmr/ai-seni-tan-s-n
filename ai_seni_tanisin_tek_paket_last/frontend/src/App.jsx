import React, { useMemo, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

const QUESTIONS = [
  {
    id: "q1",
    question: "Yeni bir ortamda nasıl davranırsın?",
    options: [
      "Önce gözlemlerim, sonra hareket ederim.",
      "İnsanlarla hızlıca iletişim kurarım.",
      "Kendi akışımda ilerlemeyi tercih ederim.",
      "Duruma göre değişir.",
    ],
  },
  {
    id: "q2",
    question: "Bir problemle karşılaştığında ilk tepkin nedir?",
    options: [
      "Önce durumu analiz ederim.",
      "Hızlı bir çözüm denerim.",
      "Başkalarının görüşünü alırım.",
      "Farklı fikirler üretmeyi denerim.",
    ],
  },
  {
    id: "q3",
    question: "Seni en çok ne motive eder?",
    options: [
      "Başarı ve ilerleme hissi.",
      "Maddi kazanç.",
      "İnsanlar üzerinde olumlu etki bırakmak.",
      "Özgür olmak.",
    ],
  },
  {
    id: "q4",
    question: "Nasıl çalışmayı tercih edersin?",
    options: [
      "Tek başıma.",
      "Küçük bir ekiple.",
      "Kalabalık bir ekip içinde.",
      "Duruma göre değişir.",
    ],
  },
  {
    id: "q5",
    question: "Karar verirken en çok neye güvenirsin?",
    options: [
      "Mantığıma.",
      "Sezgilerime.",
      "Geçmiş deneyimlerime.",
      "Başkalarının görüşlerine.",
    ],
  },
  {
    id: "q6",
    question: "Hangi çalışma tarzı sana daha yakın?",
    options: [
      "Planlı ilerlemek.",
      "Esnek ilerlemek.",
      "Risk alarak ilerlemek.",
      "Güvende kalmak.",
    ],
  },
  {
    id: "q7",
    question: "Kendini en çok hangi rolde görüyorsun?",
    options: [
      "Lider.",
      "Uzman.",
      "Üreten ve geliştiren.",
      "Destekleyici ve dengeleyici.",
    ],
  },
  {
    id: "q8",
    question: "Gelecekte kendini nerede görmek isterdin?",
    options: [
      "Daha fazla sorumluluk alan biri olarak.",
      "Belirli bir alanda uzman biri olarak.",
      "Yeni şeyler deneyen biri olarak.",
      "Henüz emin değilim.",
    ],
  },
];

export default function App() {
  const [step, setStep] = useState("welcome");
  const [name, setName] = useState("");
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const currentQuestion = QUESTIONS[questionIndex];

  const allAnswered = useMemo(
    () => QUESTIONS.every((q) => answers[q.id] !== undefined),
    [answers]
  );

  const progressPercent = useMemo(() => {
    return ((questionIndex + 1) / QUESTIONS.length) * 100;
  }, [questionIndex]);

  const setAnswer = (questionId, selectedIndex) => {
    setAnswers((prev) => ({ ...prev, [questionId]: selectedIndex }));
  };

  const resetAll = () => {
    setStep("welcome");
    setName("");
    setQuestionIndex(0);
    setAnswers({});
    setResult(null);
    setError("");
    setIsSubmitting(false);
  };

  const submitAnalysis = async () => {
    setStep("loading");
    setError("");
    setIsSubmitting(true);

    try {
      const payload = {
        name: name.trim() || "Katılımcı",
        answers: QUESTIONS.map((q) => ({
          question_id: q.id,
          selected_index: answers[q.id],
        })),
      };

      const response = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Analiz sırasında bir hata oluştu.");
      }

      const data = await response.json();
      setResult(data);
      setStep("result");
    } catch (err) {
      setError(err.message || "Bir hata oluştu.");
      setStep("welcome");
    } finally {
      setIsSubmitting(false);
    }
  };

  const nextQuestion = () => {
    if (questionIndex < QUESTIONS.length - 1) {
      setQuestionIndex((prev) => prev + 1);
    } else if (allAnswered) {
      submitAnalysis();
    }
  };

  const prevQuestion = () => {
    if (questionIndex === 0) {
      setStep("name");
    } else {
      setQuestionIndex((prev) => prev - 1);
    }
  };

  const selectedCurrentAnswer = answers[currentQuestion?.id];

  const renderWelcome = () => (
    <div className="screen screen-center fade-in">
      <div className="hero-shell">
        <div className="hero-orb orb-1" />
        <div className="hero-orb orb-2" />
        <div className="hero-orb orb-3" />

        <div className="hero-card">
          <div className="hero-logo-wrap">
            <img src="/logo2.png" alt="Logo" className="hero-logo" />
          </div>

          <div className="hero-topline">ETKİLEŞİMLİ DENEYİM</div>

          <h1 className="hero-title">
            Kendini
            <span> yapay zekânın gözünden keşfet </span>
          </h1>

          <p className="hero-subtitle">
            Sekiz kısa soru. Birkaç dakika. Güçlü yönlerini, çalışma tarzını ve
            potansiyelini yansıtan kişisel bir sonuç.
          </p>

          <div className="hero-feature-grid">
            <div className="hero-feature">
              <div className="hero-feature-title">8 kısa soru</div>
              <div className="hero-feature-text">
                Hızlı ve sade bir deneyim
              </div>
            </div>

            <div className="hero-feature">
              <div className="hero-feature-title">Kişisel içgörü</div>
              <div className="hero-feature-text">
                Cevaplarına göre şekillenen özel bir sonuç
              </div>
            </div>

            <div className="hero-feature">
              <div className="hero-feature-title">PDF rapor</div>
              <div className="hero-feature-text">
                Sonucunu link ve QR kod ile al
              </div>
            </div>
          </div>

          <div className="hero-actions">
            <button className="primary-button glow-button" onClick={() => setStep("name")}>
              Deneyimi Başlat
            </button>
          </div>

          {error ? <div className="error-box">{error}</div> : null}
        </div>
      </div>
    </div>
  );

  const renderName = () => (
    <div className="screen screen-center fade-in">
      <div className="panel name-panel">
        <div className="panel-badge">BAŞLAMADAN ÖNCE</div>

        <h2 className="panel-title">Sana nasıl hitap edelim?</h2>
        <p className="panel-subtitle">
          Bu isim sonuç ekranında ve raporunda görünecek. İstersen takma ad da kullanabilirsin.
        </p>

        <div className="input-shell">
          <input
            className="name-input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="İsmini yaz"
            maxLength={30}
          />
        </div>

        <div className="footer-actions">
          <button className="secondary-button" onClick={() => setStep("welcome")}>
            Geri
          </button>

          <button
            className="primary-button"
            onClick={() => {
              setQuestionIndex(0);
              setStep("question");
            }}
          >
            Devam Et
          </button>
        </div>
      </div>
    </div>
  );

  const renderQuestion = () => (
    <div className="question-screen fade-in">
      <div className="question-shell">
        <aside className="question-left">
          <div className="left-content">
            <h2 className="left-main-title">
              Gerçek benliğini
              <br />
              birlikte keşfedelim
            </h2>

            <p className="left-main-text">
              Soruları içtenlikle cevapla ve yapay zekânın sana dair özgün profilini oluşturmasına izin ver.
            </p>

            <div className="left-line" />

            <div className="left-info-card">
              <div className="left-info-icon">◔</div>
              <div className="left-info-text">
                <strong>Zamanını al.</strong>
                <br />
                Sana en yakın gelen seçeneği işaretle.
                <br />
                <br />
                Doğru ya da yanlış cevap yok.
                <br />
                Sadece kendin ol.
              </div>
            </div>

            <div className="left-bottom-logos">
              <img src="/logo.png" alt="Logo 1" className="left-bottom-logo" />
              <img src="/logo2.png" alt="Logo 2" className="left-bottom-logo" />
            </div>
          </div>
        </aside>

        <main className="question-right">
          <div className="question-top-progress">
            <div className="question-progress-track">
              <div
                className="question-progress-fill"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <div className="question-progress-count">
              {questionIndex + 1} / {QUESTIONS.length}
            </div>
          </div>

          <div className="question-tag">Soru {questionIndex + 1}</div>

          <h1 className="question-main-title">{currentQuestion.question}</h1>

          <div className="question-options">
            {currentQuestion.options.map((option, idx) => {
              const active = answers[currentQuestion.id] === idx;
              const letter = String.fromCharCode(65 + idx);

              return (
                <button
                  key={option}
                  type="button"
                  className={`question-option ${active ? "question-option-active" : ""}`}
                  onClick={() => setAnswer(currentQuestion.id, idx)}
                >
                  <div className="question-option-letter">{letter}</div>
                  <div className="question-option-text">{option}</div>
                </button>
              );
            })}
          </div>

          <div className="question-actions">
            <button className="question-back-btn" onClick={prevQuestion}>
              ← Geri
            </button>

            <button
              className="question-next-btn"
              onClick={nextQuestion}
              disabled={selectedCurrentAnswer === undefined || isSubmitting}
            >
              {questionIndex === QUESTIONS.length - 1 ? "Analizi Oluştur →" : "İleri →"}
            </button>
          </div>
        </main>
      </div>
    </div>
  );

  const renderLoading = () => (
    <div className="screen screen-center fade-in">
      <div className="panel loading-panel">
        <div className="scanner-ring">
          <div className="scanner-rotating-border"></div>
          <div className="scanner-ring-inner">
            <img src="/logo.png" alt="Logo" className="scanner-logo" />
          </div>
        </div>

        <div className="panel-badge">İŞLENİYOR</div>
        <h2 className="panel-title">Cevapların analiz ediliyor</h2>
        <p className="panel-subtitle loading-subtitle">
          Eğilimlerin, karar verme tarzın, çalışma şeklin ve güçlü yönlerin bir araya getiriliyor.
        </p>

        <div className="loading-words">
          <span>Davranış</span>
          <span>Motivasyon</span>
          <span>Karar Tarzı</span>
          <span>Potansiyel</span>
        </div>
      </div>
    </div>
  );

  const renderResult = () => (
    <div className="screen fade-in">
      <div className="result-layout">
        <div className="result-main">
          <div className="result-header">
            <div className="panel-badge">ANALİZ TAMAMLANDI</div>
            <h2 className="result-title">
              {name?.trim()
                ? `${name}, sende öne çıkan özellikler bunlar`
                : "Sende öne çıkan özellikler bunlar"}
            </h2>
            <p className="result-subtitle">
              Aşağıda cevaplarına göre oluşturulan profilin ve kısa yapay zekâ yorumu yer alıyor.
            </p>
          </div>

          <div className="hero-result-card">
            <div className="hero-result-label">Kısa içgörü</div>
            <p className="hero-result-text">{result.ai_result.short_summary}</p>
          </div>

          <div className="result-card-grid two-col">
            <div className="insight-card insight-card-strong">
              <div className="insight-label">Süper gücün</div>
              <div className="insight-text">{result.ai_result.super_power}</div>
            </div>

            <div className="insight-card insight-card-warning">
              <div className="insight-label">Seni zorlayabilecek nokta</div>
              <div className="insight-text">{result.ai_result.blocking_point}</div>
            </div>
          </div>

          <div className="result-card-grid two-col">
            <div className="glass-card">
              <h3 className="section-title">Profilin</h3>
              <div className="profile-list">
                <div className="profile-row">
                  <span>Sosyallik</span>
                  <strong>{result.profile.social}</strong>
                </div>
                <div className="profile-row">
                  <span>Karar tarzı</span>
                  <strong>{result.profile.decision}</strong>
                </div>
                <div className="profile-row">
                  <span>Motivasyon</span>
                  <strong>{result.profile.motivation}</strong>
                </div>
                <div className="profile-row">
                  <span>Çalışma tarzı</span>
                  <strong>{result.profile.work_style}</strong>
                </div>
                <div className="profile-row">
                  <span>Rol</span>
                  <strong>{result.profile.role}</strong>
                </div>
              </div>
            </div>

            <div className="glass-card">
              <h3 className="section-title">Sana uygun alanlar</h3>
              <div className="suggestion-list">
                {result.ai_result.career_suggestions.map((item) => (
                  <div key={item} className="suggestion-item">
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="glass-card">
            <h3 className="section-title">Önerilen meslek</h3>
            <div className="suggestion-list">
              <div className="suggestion-item">
                {result.ai_result.job_suggestion}
              </div>
            </div>
          </div>

          <div className="glass-card story-card">
            <h3 className="section-title">5 yıl sonra sen</h3>
            <p className="story-text">{result.ai_result.five_year_story}</p>
          </div>
        </div>

        <div className="result-side">
          <div className="glass-card qr-card">
            <div className="qr-title">Raporunu al</div>


            <a
              href={result.pdf_url}
              target="_blank"
              rel="noreferrer"
              className="primary-link-button"
            >
              PDF&apos;i Aç
            </a>
          </div>

          <button className="secondary-button full-width" onClick={resetAll}>
            Yeni Kullanıcı İçin Sıfırla
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="app-root">
      <style>{`
        * {
          box-sizing: border-box;
        }

        html, body, #root {
          width: 100%;
          min-height: 100%;
          margin: 0;
          padding: 0;
          font-family: Inter, Arial, Helvetica, sans-serif;
          background: #070b16;
        }

        body {
          overflow-x: hidden;
        }

        button,
        input,
        a {
          font-family: inherit;
        }

        .app-root {
          min-height: 100vh;
          color: #f8fafc;
          position: relative;
          background:
            radial-gradient(circle at 15% 20%, rgba(122, 92, 255, 0.26), transparent 28%),
            radial-gradient(circle at 80% 18%, rgba(41, 182, 246, 0.22), transparent 24%),
            radial-gradient(circle at 72% 78%, rgba(236, 72, 153, 0.15), transparent 24%),
            linear-gradient(135deg, #060816 0%, #0b1020 45%, #11172b 100%);
        }

        .app-root::before {
          content: "";
          position: fixed;
          inset: 0;
          pointer-events: none;
          background-image:
            linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
          background-size: 34px 34px;
          mask-image: radial-gradient(circle at center, black 38%, transparent 95%);
          opacity: 0.35;
        }

        .screen {
          min-height: 100vh;
          position: relative;
          z-index: 2;
          padding: 36px;
        }

        .screen-center {
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .fade-in {
          animation: fadeInUp 0.55s ease;
        }

        .hero-shell {
          width: 100%;
          max-width: 1380px;
          min-height: calc(100vh - 72px);
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
          border-radius: 36px;
          border: 1px solid rgba(255,255,255,0.08);
          background:
            linear-gradient(145deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
          box-shadow:
            0 30px 80px rgba(0,0,0,0.45),
            inset 0 1px 0 rgba(255,255,255,0.06);
          backdrop-filter: blur(18px);
        }

        .hero-card {
          position: relative;
          z-index: 3;
          width: 100%;
          max-width: 980px;
          padding: 56px;
          text-align: center;
        }

.hero-logo-wrap {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 290px;
  height: 290px;
  margin: 0 auto 18px;
  border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.2);
  box-shadow: 0 8px 30px rgba(99,102,241,0.35);
  background: rgba(255,255,255,0.05);
  overflow: hidden;   /* 🔥 önemli */
}

.hero-logo {
  width: 100%;
  height: 100%;
  object-fit: cover;

  transform: scale(1.2) translateX(5px) translateY(8px);
  transform-origin: center;
}

        .hero-topline,
        .panel-badge {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 8px 14px;
          border-radius: 999px;
          background: rgba(255,255,255,0.08);
          border: 1px solid rgba(255,255,255,0.12);
          color: #cbd5e1;
          font-size: 12px;
          font-weight: 700;
          letter-spacing: 0.16em;
          text-transform: uppercase;
        }

        .hero-title {
          margin: 24px 0 18px;
          font-size: clamp(48px, 6vw, 82px);
          line-height: 1.04;
          font-weight: 800;
          letter-spacing: -0.04em;
          color: #ffffff;
        }

        .hero-title span {
          display: block;
          background: linear-gradient(90deg, #7dd3fc 0%, #c084fc 52%, #f9a8d4 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .hero-subtitle {
          max-width: 760px;
          margin: 0 auto 34px;
          font-size: 22px;
          line-height: 1.75;
          color: #c7d2fe;
        }

        .hero-feature-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 18px;
          margin: 0 auto 34px;
        }

        .hero-feature {
          padding: 22px 20px;
          border-radius: 24px;
          background: rgba(255,255,255,0.06);
          border: 1px solid rgba(255,255,255,0.10);
          backdrop-filter: blur(12px);
          text-align: left;
        }

        .hero-feature-title {
          font-size: 18px;
          font-weight: 700;
          margin-bottom: 8px;
          color: #ffffff;
        }

        .hero-feature-text {
          font-size: 15px;
          line-height: 1.7;
          color: #cbd5e1;
        }

        .hero-actions {
          display: flex;
          justify-content: center;
        }

        .hero-orb {
          position: absolute;
          border-radius: 999px;
          filter: blur(18px);
          opacity: 0.8;
        }

        .orb-1 {
          width: 280px;
          height: 280px;
          top: 6%;
          left: 7%;
          background: radial-gradient(circle, rgba(96,165,250,0.65), rgba(96,165,250,0));
          animation: floatOrb 7s ease-in-out infinite;
        }

        .orb-2 {
          width: 340px;
          height: 340px;
          right: 8%;
          top: 12%;
          background: radial-gradient(circle, rgba(168,85,247,0.55), rgba(168,85,247,0));
          animation: floatOrb 9s ease-in-out infinite reverse;
        }

        .orb-3 {
          width: 280px;
          height: 280px;
          bottom: 8%;
          left: 32%;
          background: radial-gradient(circle, rgba(244,114,182,0.40), rgba(244,114,182,0));
          animation: pulseOrb 6s ease-in-out infinite;
        }

        .panel {
          width: 100%;
          max-width: 860px;
          padding: 40px;
          border-radius: 32px;
          border: 1px solid rgba(255,255,255,0.1);
          background:
            linear-gradient(145deg, rgba(255,255,255,0.09), rgba(255,255,255,0.04));
          box-shadow:
            0 24px 60px rgba(0,0,0,0.4),
            inset 0 1px 0 rgba(255,255,255,0.06);
          backdrop-filter: blur(18px);
        }

        .name-panel {
          max-width: 760px;
        }

        .panel-title {
          margin: 18px 0 10px;
          font-size: 42px;
          line-height: 1.15;
          letter-spacing: -0.03em;
          color: #ffffff;
        }

        .panel-subtitle {
          margin: 0 0 26px;
          font-size: 18px;
          line-height: 1.8;
          color: #cbd5e1;
        }

        .input-shell {
          position: relative;
          margin-top: 10px;
        }

        .name-input {
          width: 100%;
          height: 74px;
          padding: 0 24px;
          border-radius: 22px;
          border: 1px solid rgba(255,255,255,0.12);
          background: rgba(255,255,255,0.06);
          color: #ffffff;
          font-size: 22px;
          outline: none;
          transition: all 0.25s ease;
        }

        .name-input::placeholder {
          color: #94a3b8;
        }

        .name-input:focus {
          border-color: rgba(125, 211, 252, 0.6);
          box-shadow: 0 0 0 4px rgba(125, 211, 252, 0.12);
          background: rgba(255,255,255,0.08);
        }

        .question-screen {
          min-height: 100vh;
          padding: 0;
          background: #f5f7fb;
          position: relative;
          z-index: 2;
        }

        .question-shell {
          min-height: 100vh;
          display: grid;
          grid-template-columns: 320px 1fr;
        }

        .question-left {
          background: linear-gradient(180deg, #0d1950 0%, #0b1440 100%);
          color: #ffffff;
          padding: 28px 26px;
          display: flex;
          flex-direction: column;
          justify-content: flex-start;
        }

        .left-content {
          margin-top: 22px;
        }

        .left-main-title {
          font-size: 32px;
          line-height: 1.15;
          font-weight: 800;
          letter-spacing: -0.03em;
          margin: 0 0 20px;
          color: #ffffff;
        }

        .left-main-text {
          font-size: 15px;
          line-height: 1.9;
          color: rgba(255,255,255,0.78);
          max-width: 220px;
          margin: 0;
        }

        .left-line {
          width: 64px;
          height: 3px;
          border-radius: 999px;
          margin: 28px 0;
          background: linear-gradient(90deg, #4ea7ff, #8b5cf6);
        }

        .left-info-card {
          width: 100%;
          max-width: 250px;
          border-radius: 18px;
          background: rgba(255,255,255,0.06);
          padding: 18px 16px;
          border: 1px solid rgba(255,255,255,0.05);
        }

        .left-info-icon {
          font-size: 15px;
          margin-bottom: 10px;
          opacity: 0.9;
        }

        .left-info-text {
          font-size: 14px;
          line-height: 1.75;
          color: rgba(255,255,255,0.92);
        }

        .left-bottom-logos {
          margin-top: 24px;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
        }

        .left-bottom-logo {
          width: 250px;
          height: 250px;
          object-fit: contain;
          border-radius: 12px;
          background: #ffffff;
          padding: 14px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.18);
        }

        .question-right {
          background: #f5f7fb;
          padding: 30px 38px 32px;
          display: flex;
          flex-direction: column;
        }

        .question-top-progress {
          display: flex;
          align-items: center;
          gap: 18px;
          margin-bottom: 22px;
        }

        .question-progress-track {
          flex: 1;
          height: 6px;
          border-radius: 999px;
          background: #d9dce3;
          overflow: hidden;
        }

        .question-progress-fill {
          height: 100%;
          border-radius: 999px;
          background: linear-gradient(90deg, #67b7ff 0%, #8b5cf6 55%, #ec4899 100%);
        }

        .question-progress-count {
          font-size: 13px;
          font-weight: 600;
          color: #7c8597;
          min-width: 40px;
          text-align: right;
        }

        .question-tag {
          font-size: 13px;
          color: #6d73ff;
          margin-bottom: 10px;
        }

        .question-main-title {
          font-size: 34px;
          line-height: 1.22;
          letter-spacing: -0.03em;
          color: #101828;
          margin: 0 0 28px;
          font-weight: 800;
        }

        .question-options {
          display: flex;
          flex-direction: column;
          gap: 14px;
          max-width: 100%;
        }

        .question-option {
          width: 100%;
          min-height: 74px;
          border-radius: 16px;
          border: 1px solid #e3e6ee;
          background: #ffffff;
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 0 18px 0 14px;
          cursor: pointer;
          transition: all 0.2s ease;
          text-align: left;
        }

        .question-option:hover {
          border-color: #cfd5e4;
          transform: translateY(-1px);
        }

        .question-option-active {
          border-color: #7c73ff;
          background: #f2f4ff;
          box-shadow: 0 0 0 1px rgba(124,115,255,0.08) inset;
        }

        .question-option-letter {
          width: 38px;
          height: 38px;
          min-width: 38px;
          border-radius: 999px;
          background: #eef1f6;
          color: #8b93a6;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 800;
          font-size: 16px;
        }

        .question-option-active .question-option-letter {
          background: #e6e9ff;
          color: #6d73ff;
        }

        .question-option-text {
          font-size: 16px;
          color: #1f2937;
          line-height: 1.5;
          font-weight: 500;
        }

        .question-actions {
          margin-top: 26px;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .question-back-btn {
          border: none;
          background: #e8ebf0;
          color: #495266;
          height: 44px;
          padding: 0 18px;
          border-radius: 12px;
          font-weight: 600;
          cursor: pointer;
        }

        .question-next-btn {
          border: none;
          background: linear-gradient(90deg, #4f8cff 0%, #7c4dff 100%);
          color: #ffffff;
          height: 44px;
          padding: 0 24px;
          border-radius: 12px;
          font-weight: 700;
          cursor: pointer;
          box-shadow: 0 8px 20px rgba(99,102,241,0.18);
        }

        .question-next-btn:disabled {
          opacity: 0.45;
          cursor: not-allowed;
          box-shadow: none;
        }

        .footer-actions {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 14px;
          margin-top: 30px;
        }

        .primary-button,
        .secondary-button,
        .primary-link-button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-height: 62px;
          padding: 0 28px;
          border-radius: 18px;
          font-size: 17px;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.25s ease;
          text-decoration: none;
        }

        .primary-button {
          border: none;
          color: #ffffff;
          background: linear-gradient(90deg, #2563eb 0%, #7c3aed 55%, #db2777 100%);
          box-shadow: 0 14px 34px rgba(99,102,241,0.35);
        }

        .primary-button:hover {
          transform: translateY(-2px) scale(1.01);
          box-shadow: 0 18px 40px rgba(99,102,241,0.42);
        }

        .primary-button:disabled {
          opacity: 0.45;
          cursor: not-allowed;
          transform: none;
          box-shadow: none;
        }

        .glow-button {
          min-width: 250px;
          min-height: 68px;
          font-size: 19px;
        }

        .secondary-button {
          border: 1px solid rgba(255,255,255,0.14);
          background: rgba(255,255,255,0.05);
          color: #f8fafc;
          backdrop-filter: blur(8px);
        }

        .secondary-button:hover {
          transform: translateY(-2px);
          background: rgba(255,255,255,0.08);
        }

        .full-width {
          width: 100%;
        }

        .loading-panel {
          max-width: 720px;
          text-align: center;
          padding: 50px 40px;
        }

        .scanner-ring {
          position: relative;
          width: 120px;
          height: 120px;
          margin: 0 auto 28px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .scanner-rotating-border {
          position: absolute;
          inset: 0;
          border-radius: 50%;
          background: conic-gradient(from 0deg, #38bdf8, #8b5cf6, #ec4899, #38bdf8);
          animation: spin 2.2s linear infinite;
          box-shadow: 0 0 36px rgba(99,102,241,0.28);
        }

        .scanner-ring-inner {
          position: relative;
          z-index: 2;
          width: calc(100% - 6px);
          height: calc(100% - 6px);
          border-radius: 50%;
          background: #0c1222;
          border: 1px solid rgba(255,255,255,0.08);
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
        }

        .scanner-logo {
          width: 120px;
          height: 120px;
          object-fit: cover;
          border-radius: 50%;
          background: #ffffff;
          padding: 6px;
        }

        .loading-subtitle {
          max-width: 560px;
          margin-left: auto;
          margin-right: auto;
        }

        .loading-words {
          display: flex;
          flex-wrap: wrap;
          justify-content: center;
          gap: 12px;
          margin-top: 24px;
        }

        .loading-words span {
          padding: 10px 14px;
          border-radius: 999px;
          background: rgba(255,255,255,0.06);
          border: 1px solid rgba(255,255,255,0.10);
          color: #dbeafe;
          font-size: 14px;
        }

        .result-layout {
          width: 100%;
          max-width: 1460px;
          margin: 0 auto;
          min-height: calc(100vh - 72px);
          display: grid;
          grid-template-columns: minmax(0, 1fr) 360px;
          gap: 24px;
          align-items: start;
        }

        .result-main {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .result-side {
          display: flex;
          flex-direction: column;
          gap: 18px;
          position: sticky;
          top: 36px;
        }

        .result-header {
          margin-bottom: 2px;
        }

        .result-title {
          margin: 18px 0 10px;
          font-size: clamp(34px, 4vw, 58px);
          line-height: 1.08;
          letter-spacing: -0.04em;
          color: #ffffff;
        }

        .result-subtitle {
          margin: 0;
          max-width: 850px;
          color: #cbd5e1;
          font-size: 18px;
          line-height: 1.8;
        }

        .hero-result-card,
        .glass-card,
        .insight-card {
          border-radius: 28px;
          border: 1px solid rgba(255,255,255,0.1);
          background:
            linear-gradient(145deg, rgba(255,255,255,0.08), rgba(255,255,255,0.04));
          box-shadow:
            0 22px 54px rgba(0,0,0,0.34),
            inset 0 1px 0 rgba(255,255,255,0.05);
          backdrop-filter: blur(16px);
        }

        .hero-result-card {
          padding: 28px;
        }

        .hero-result-label,
        .insight-label {
          font-size: 13px;
          font-weight: 800;
          letter-spacing: 0.16em;
          text-transform: uppercase;
          color: #93c5fd;
          margin-bottom: 12px;
        }

        .hero-result-text {
          margin: 0;
          font-size: 26px;
          line-height: 1.7;
          letter-spacing: -0.02em;
          color: #f8fafc;
        }

        .result-card-grid {
          display: grid;
          gap: 20px;
        }

        .two-col {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .insight-card {
          padding: 24px;
        }

        .insight-card-strong {
          background:
            linear-gradient(145deg, rgba(16,185,129,0.16), rgba(255,255,255,0.05));
        }

        .insight-card-warning {
          background:
            linear-gradient(145deg, rgba(244,63,94,0.14), rgba(255,255,255,0.05));
        }

        .insight-text {
          font-size: 22px;
          line-height: 1.7;
          color: #ffffff;
        }

        .glass-card {
          padding: 24px;
        }

        .section-title {
          margin: 0 0 18px;
          font-size: 24px;
          color: #ffffff;
        }

        .profile-list {
          display: grid;
          gap: 12px;
        }

        .profile-row {
          display: flex;
          justify-content: space-between;
          gap: 14px;
          padding: 14px 16px;
          border-radius: 16px;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.06);
          font-size: 17px;
          color: #cbd5e1;
        }

        .profile-row strong {
          color: #ffffff;
          text-align: right;
        }

        .suggestion-list {
          display: grid;
          gap: 12px;
        }

        .suggestion-item {
          padding: 16px 18px;
          border-radius: 16px;
          background: linear-gradient(135deg, rgba(59,130,246,0.12), rgba(168,85,247,0.10));
          border: 1px solid rgba(255,255,255,0.08);
          font-size: 18px;
          color: #f8fafc;
        }

        .story-card {
          padding-top: 26px;
        }

        .story-text {
          margin: 0;
          font-size: 20px;
          line-height: 1.9;
          color: #e2e8f0;
        }

        .qr-card {
          text-align: center;
          padding: 24px;
        }

        .qr-title {
          font-size: 28px;
          font-weight: 800;
          color: #ffffff;
          margin-bottom: 10px;
        }

        .qr-subtitle {
          font-size: 16px;
          line-height: 1.7;
          color: #cbd5e1;
          margin-bottom: 18px;
        }

        .qr-image-wrap {
          width: 100%;
          padding: 16px;
          border-radius: 24px;
          background: rgba(255,255,255,0.88);
          margin-bottom: 18px;
          box-shadow: inset 0 1px 0 rgba(255,255,255,0.8);
        }

        .qr-image {
          width: 100%;
          max-width: 250px;
          aspect-ratio: 1 / 1;
          object-fit: contain;
          display: block;
          margin: 0 auto;
          border-radius: 18px;
        }

        .primary-link-button {
          width: 100%;
          color: #ffffff;
          background: linear-gradient(90deg, #2563eb 0%, #7c3aed 55%, #db2777 100%);
          box-shadow: 0 14px 34px rgba(99,102,241,0.35);
        }

        .primary-link-button:hover {
          transform: translateY(-2px);
          box-shadow: 0 18px 40px rgba(99,102,241,0.42);
        }

        .error-box {
          margin-top: 18px;
          padding: 14px 16px;
          border-radius: 16px;
          background: rgba(127,29,29,0.25);
          border: 1px solid rgba(248,113,113,0.35);
          color: #fecaca;
          font-size: 15px;
        }

        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(16px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        @keyframes floatOrb {
          0%, 100% {
            transform: translateY(0px) translateX(0px);
          }
          50% {
            transform: translateY(-18px) translateX(10px);
          }
        }

        @keyframes pulseOrb {
          0%, 100% {
            transform: scale(1);
            opacity: 0.75;
          }
          50% {
            transform: scale(1.08);
            opacity: 1;
          }
        }

        @media (max-width: 1200px) {
          .hero-feature-grid,
          .two-col,
          .result-layout {
            grid-template-columns: 1fr;
          }

          .result-side {
            position: static;
          }
        }

        @media (max-width: 1100px) {
          .question-shell {
            grid-template-columns: 1fr;
          }

          .left-main-text,
          .left-info-card {
            max-width: none;
          }

          .question-right {
            padding: 26px 20px 28px;
          }

          .question-main-title {
            font-size: 28px;
          }
        }

        @media (max-width: 768px) {
          .screen {
            padding: 18px;
          }

          .hero-card,
          .panel {
            padding: 26px;
          }

          .hero-title {
            font-size: 42px;
          }

          .panel-title,
          .result-title {
            font-size: 32px;
          }

          .hero-result-text,
          .insight-text,
          .story-text {
            font-size: 18px;
          }

          .footer-actions {
            flex-direction: column;
          }

          .primary-button,
          .secondary-button {
            width: 100%;
          }
        }
      `}</style>

      {step === "welcome" && renderWelcome()}
      {step === "name" && renderName()}
      {step === "question" && renderQuestion()}
      {step === "loading" && renderLoading()}
      {step === "result" && result && renderResult()}
    </div>
  );
}