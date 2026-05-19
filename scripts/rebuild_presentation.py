"""Reemplaza el cuerpo de diapositivas en docs/presentacion.html."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "docs" / "presentacion.html"

SLIDES = """
<!-- SLIDE 01 — Nombre del proyecto -->
<section class="slide masthead" id="slide-01" data-slide="1">
  <div class="masthead-inner">
    <div class="slide-num" style="color:rgba(245,240,232,0.5)">01 / 08 · ~2 min</div>
    <div class="course-label">Maestría en Ciencias de los Datos · Proyecto Integrador II</div>
    <h1>Run<span>Audit</span></h1>
    <p class="subtitle">Validación masiva de garantías vehiculares frente al RUNT</p>
    <div class="course-meta">
      <div>
        <span class="meta-label">Enfoque</span>
        <span class="meta-value">OCR (CRNN+CTC) + web scraping + AWS</span>
      </div>
      <div>
        <span class="meta-label">Sector</span>
        <span class="meta-value">Crédito con garantía vehicular</span>
      </div>
      <div>
        <span class="meta-label">Presentación</span>
        <span class="meta-value">20 minutos · 8 diapositivas</span>
      </div>
    </div>
    <div class="badge">Automatización de consulta al RUNT — proyecto académico</div>
  </div>
</section>

<!-- SLIDE 02 — Integrantes -->
<section class="slide" id="slide-02" data-slide="2">
  <div class="container">
    <div class="slide-num">02 / 08 · ~1 min</div>
    <span class="time-badge">Integrantes</span>
    <h2>Equipo</h2>
    <div class="team-grid">
      <div class="team-card">
        <div class="name">David Botero</div>
        <div class="role">Integrante</div>
      </div>
      <div class="team-card">
        <div class="name">Jorge Giraldo</div>
        <div class="role">Integrante</div>
      </div>
      <div class="team-card">
        <div class="name">Samuel Padierna</div>
        <div class="role">Integrante</div>
      </div>
    </div>
  </div>
</section>

<!-- SLIDE 03 — Problema y fuentes -->
<section class="slide" id="slide-03" data-slide="3">
  <div class="container">
    <div class="slide-num">03 / 08 · ~3 min</div>
    <div class="slide-header">
      <div class="big-num">03</div>
      <div>
        <span class="time-badge">Problema y fuentes de datos</span>
        <h2>El cuello de botella del CAPTCHA</h2>
      </div>
    </div>
    <div class="two-col">
      <div>
        <div class="pullquote"><p>Las entidades que otorgan crédito con garantía vehicular deben auditar su portafolio contra el RUNT, fuente oficial de propietario, características y garantías prendarias.</p></div>
        <ul class="compact-list">
          <li>El portal del RUNT exige <strong>CAPTCHA visual</strong> → bloquea automatización.</li>
          <li>Proceso actual <strong>manual</strong> (placa por placa): inviable con decenas de miles de vehículos.</li>
          <li>Riesgo: exposición crediticia no detectada e información desactualizada.</li>
        </ul>
      </div>
      <div class="overview-box">
        <h3>Fuentes de datos</h3>
        <ul>
          <li><strong>RUNT</strong> — consulta web (salida: datos del vehículo)</li>
          <li><strong>Excel del banco</strong> — <code>numero_placas</code>, <code>cod_id</code>, <code>id</code></li>
          <li><strong>Imágenes captcha etiquetadas</strong> — 3.457 PNG para entrenar el OCR (nombre = etiqueta)</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<!-- SLIDE 04 — EDA -->
<section class="slide" id="slide-04" data-slide="4">
  <div class="container">
    <div class="slide-num">04 / 08 · ~3 min</div>
    <div class="slide-header">
      <div class="big-num">04</div>
      <div>
        <span class="time-badge">Análisis exploratorio (EDA)</span>
        <h2>Dataset de captchas: etiquetado y limpieza</h2>
        <p>EDA orientado a visión: calidad de imagen, etiquetas y pipeline de preproceso.</p>
      </div>
    </div>
    <div class="two-col">
      <div class="overview-box">
        <h3>Etiquetado</h3>
        <ul>
          <li>PNG con nombre = texto del captcha (ej. <code>h2Yg8.png</code>)</li>
          <li>3.457 muestras · 56 caracteres (sin 0/O/1/I/L)</li>
          <li>Split 90% train / 10% validación</li>
        </ul>
        <h3 style="margin-top:16px">Limpieza (OpenCV)</h3>
        <ul>
          <li>Grises → bilateral → <strong>CLAHE</strong></li>
          <li>Umbral adaptativo → mediana → <strong>280×80 px</strong></li>
        </ul>
      </div>
      <div class="figure-block">
        <img src="assets/modelo-preproceso.png" alt="Pipeline de limpieza del captcha" width="480">
        <p class="figure-caption">Entrada → suavizado/CLAHE → binarizado para el modelo</p>
      </div>
    </div>
  </div>
</section>

<!-- SLIDE 05 — Modelado -->
<section class="slide" id="slide-05" data-slide="5">
  <div class="container">
    <div class="slide-num">05 / 08 · ~4 min</div>
    <div class="slide-header">
      <div class="big-num">05</div>
      <div>
        <span class="time-badge">Modelado</span>
        <h2>CRNN + CTC (aprendizaje profundo)</h2>
        <p>CNN + BiLSTM + CTC: reconocimiento de secuencias sin segmentar cada carácter a mano.</p>
      </div>
    </div>
    <div class="mermaid-wrap">
      <pre class="mermaid">flowchart LR
    Img[Captcha 280x80] --> CNN[Conv2D + MaxPool]
    CNN --> BiLSTM[BiLSTM x2]
    BiLSTM --> CTC[CTC decode]
    CTC --> Text[5 caracteres]</pre>
    </div>
    <div class="figure-block">
      <img src="assets/modelo-predicciones-muestra.png" alt="Predicciones del modelo" style="max-height:200px">
      <p class="figure-caption">Validación visual: predicción vs. captcha real</p>
    </div>
    <div class="tag-list">
      <span class="tag">TensorFlow / Keras</span>
      <span class="tag">Modelo Experimental.ipynb</span>
      <span class="tag">captcha_model.keras</span>
    </div>
  </div>
</section>

<!-- SLIDE 06 — Despliegue -->
<section class="slide" id="slide-06" data-slide="6">
  <div class="container">
    <div class="slide-num">06 / 08 · ~4 min</div>
    <div class="slide-header">
      <div class="big-num">06</div>
      <div>
        <span class="time-badge">Despliegue</span>
        <h2>Arquitectura AWS y prototipo local</h2>
      </div>
    </div>
    <div class="mermaid-wrap">
      <pre class="mermaid">flowchart TB
    Excel[Excel placas] --> S3in[S3 input]
    S3in --> Split[split_excel]
    Split --> SQS[SQS]
    SQS --> Worker[ECS Playwright+OCR]
    Worker --> S3out[S3 JSON]
    Worker --> DDB[DynamoDB]</pre>
    </div>
    <div class="pipeline">
      <div class="pipeline-step"><div class="step-n">1</div><h4>Ingesta</h4><p>S3 + job_id</p></div>
      <div class="pipeline-step"><div class="step-n">2</div><h4>Cola</h4><p>SQS + DLQ</p></div>
      <div class="pipeline-step"><div class="step-n">3</div><h4>Worker</h4><p>RUNT + JSON</p></div>
    </div>
  </div>
</section>

<!-- SLIDE 07 — Resultados -->
<section class="slide" id="slide-07" data-slide="7">
  <div class="container">
    <div class="slide-num">07 / 08 · ~2 min</div>
    <div class="slide-header">
      <div class="big-num">07</div>
      <div>
        <span class="time-badge">Resultados</span>
        <h2>Lo logrado</h2>
      </div>
    </div>
    <div class="metric-row">
      <div class="metric-card"><div class="val">2.676</div><div class="lbl">Captchas etiquetados</div></div>
      <div class="metric-card"><div class="val">1.000+</div><div class="lbl">Placas por job</div></div>
      <div class="metric-card"><div class="val">E2E</div><div class="lbl">Excel → SQS → worker</div></div>
    </div>
    <div class="overview-box">
      <h3>Entregables</h3>
      <ul>
        <li>OCR integrado en worker + scraper Playwright RUNT</li>
        <li>Orquestador e infra Floci (S3, SQS, DynamoDB)</li>
        <li>Demo reproducible y docs/arquitectura.md</li>
      </ul>
    </div>
  </div>
</section>

<!-- SLIDE 08 — Conclusiones -->
<section class="slide" id="slide-08" data-slide="8">
  <div class="container">
    <div class="slide-num">08 / 08 · ~1 min</div>
    <div class="slide-header">
      <div class="big-num">08</div>
      <div>
        <span class="time-badge">Conclusiones</span>
        <h2>Cierre</h2>
      </div>
    </div>
    <div class="overview-box">
      <ul>
        <li>El CAPTCHA bloquea la auditoría masiva; el OCR + scraping la hace viable.</li>
        <li>Arquitectura por colas escala lotes grandes en AWS.</li>
        <li>EDA de imágenes (etiquetado + limpieza) determina la calidad del modelo.</li>
        <li>Próximos pasos: más captchas, despliegue AWS real, cumplimiento legal RUNT.</li>
      </ul>
    </div>
    <div class="pullquote" style="margin-top:24px"><p>RunAudit: de consultas manuales a un pipeline automatizado y auditable.</p></div>
    <p style="margin-top:20px;font-family:'DM Mono',monospace;font-size:12px;color:var(--muted)">¿Preguntas?</p>
  </div>
</section>
""".replace("", "").replace("", "")


def main() -> None:
    html = HTML.read_text(encoding="utf-8")
    start = html.index("<!-- SLIDE 01")
    end = html.index('<nav class="presenter-nav"')
    html = html[:start] + SLIDES.strip() + "\n\n" + html[end:]
    html = html.replace('<span id="slide-counter">01 / 14</span>', '<span id="slide-counter">01 / 08</span>')
    HTML.write_text(html, encoding="utf-8")
    print("OK:", html.count('data-slide='), "slides")


if __name__ == "__main__":
    main()
