/* Evidence viewer only: no geocoding, uploads, tracking, or persistence. */
"use strict";
const $ = (id) => document.getElementById(id);
const state = { language: "en", data: null, materialIndex: 0, caseIndex: 0, images: new Map(), zoom: 100, imageError: false };
const loopback = ["localhost", "127.0.0.1", "::1", "[::1]"].includes(location.hostname);
const privateReview = loopback && new URLSearchParams(location.search).get("review") === "1";
const localPaths = ["/__local_materials/terrain.png", "/__local_materials/imagery.png", "/__local_materials/sketch.jpg"];
const languageText = (en, zh) => state.language === "en" ? en : zh;
const field = (row, key, fallback = "") => String(row?.[`${key}_${state.language}`] ?? row?.[key] ?? fallback);
const node = (tag, className, text) => { const element = document.createElement(tag); if (className) element.className = className; if (text !== undefined) element.textContent = String(text); return element; };
const unknown = () => languageText("Unable to verify", "无法验证");
function sourceLink(id) { const a = node("a", "", id); a.href = `#source-${id}`; return a; }
function plain(value) { if (value === null || value === undefined || value === "") return unknown(); if (typeof value === "object") return String(value.rating ?? value.status ?? value.judgment ?? JSON.stringify(value)); return String(value); }
function statusLabel(status) {
  const labels = {
    source_backed_evaluation: ["SOURCE-BACKED EVALUATION", "来源支持的评估"],
    source_supported: ["SOURCE-SUPPORTED DRAFT", "来源支持草稿"],
    source_backed_draft: ["SOURCE-BACKED DRAFT", "来源支持草稿"],
    source_backed_reframing: ["SOURCE-BACKED REFRAMING", "同源功能辨析"],
    boundary_exercise: ["BOUNDARY EXERCISE", "证据边界练习"],
    evidence_boundary_exercise: ["BOUNDARY EXERCISE", "证据边界练习"],
    evidence_limited: ["EVIDENCE-LIMITED", "证据有限"],
    pending_current_evidence: ["CURRENT EVIDENCE PENDING", "待补当前证据"],
    pending_evidence: ["PENDING EVIDENCE", "待补证"],
    pending: ["PENDING EVIDENCE", "待补证"],
  };
  const pair = labels[status]; return pair ? languageText(...pair) : languageText("REVIEW DRAFT", "审阅草稿");
}
function syncStatic() {
  document.documentElement.lang = state.language === "en" ? "en" : "zh-CN";
  document.querySelectorAll("[data-en][data-zh]").forEach((el) => { el.textContent = el.dataset[state.language]; });
  $("language").textContent = state.language === "en" ? "中文 ↗" : "EN ↗";
  $("language").setAttribute("aria-label", state.language === "en" ? "Switch to Chinese" : "切换至英文");
  $("material-tabs").setAttribute("aria-label", languageText("Map materials", "地图材料"));
  $("case-tabs").setAttribute("aria-label", languageText("Evaluation cases", "评估案例"));
}
function renderMaterialTabs() {
  const container = $("material-tabs"); container.replaceChildren();
  state.data.materials.forEach((material, index) => {
    const button = node("button", "material-tab"); button.type = "button"; button.id = `material-tab-${index}`;
    button.setAttribute("role", "tab"); button.setAttribute("aria-controls", "material-panel");
    button.setAttribute("aria-selected", index === state.materialIndex ? "true" : "false"); button.tabIndex = index === state.materialIndex ? 0 : -1;
    const copy = node("span"); copy.append(node("strong", "", field(material, "title")), node("small", "", field(material, "label")));
    button.append(node("span", "tab-number", `0${index + 1}`), copy);
    button.addEventListener("click", () => selectMaterial(index));
    button.addEventListener("keydown", (event) => arrowTab(event, index, state.data.materials.length, selectMaterial, "material-tab-"));
    container.append(button);
  });
}
function arrowTab(event, index, count, select, prefix) {
  let next = index;
  if (["ArrowRight", "ArrowDown"].includes(event.key)) next = (index + 1) % count;
  else if (["ArrowLeft", "ArrowUp"].includes(event.key)) next = (index - 1 + count) % count;
  else if (event.key === "Home") next = 0;
  else if (event.key === "End") next = count - 1;
  else return;
  event.preventDefault(); select(next); $(prefix + next).focus();
}
function selectMaterial(index) { state.materialIndex = index; state.zoom = 100; state.imageError = false; renderMaterialTabs(); renderMaterial(); }
function materialPlaceholder(material) {
  const div = $("material-placeholder"); div.replaceChildren();
  const observation = node("div", "observation");
  observation.append(node("span", "mono", languageText("OBSERVED LABEL", "图中可见标注")), node("strong", "", field(material, "observed_label", state.materialIndex === 2 ? "老太箐地图" : "老太箐")), node("p", "", field(material, "label")));
  const explanation = node("p", "inference-note", languageText("Original image excluded while source rights are reviewed. The visible label can be discussed; a precise reading-space location cannot be inferred.", "原图在来源许可审核期间不随仓库分发。可讨论图中可见标注，不能据此推算书苑精确位置。"));
  div.append(observation, explanation);
}
function renderMaterial() {
  const material = state.data.materials[state.materialIndex];
  $("material-panel").setAttribute("aria-labelledby", `material-tab-${state.materialIndex}`);
  $("material-caption").textContent = `${material.id} / ${field(material, "title")}`;
  materialPlaceholder(material);
  const localImage = state.images.get(state.materialIndex);
  const image = $("material-image");
  image.alt = `${field(material, "title")} — ${languageText("unregistered reference image, not a verified map pin", "未配准参考图，不是已核实点位")}`;
  image.hidden = !localImage || state.imageError;
  $("material-placeholder").hidden = Boolean(localImage) && !state.imageError;
  if (localImage && !state.imageError) { if (image.getAttribute("src") !== localImage.url) image.src = localImage.url; }
  else image.removeAttribute("src");
  $("local-review-notice").hidden = !privateReview;
  const details = $("material-details"); details.replaceChildren();
  const observed = node("div"); observed.append(node("p", "eyebrow", languageText("WHAT THE MATERIAL SUPPORTS", "材料可支持什么")), node("p", "", field(material, "supports", field(material, "label"))));
  const sourceLinks = node("div", "case-source-links"); (material.source_ids ?? []).forEach((id) => sourceLinks.append(sourceLink(id))); observed.append(sourceLinks);
  if (material.width && material.height) observed.append(node("p", "mono material-dimensions", `${material.width} × ${material.height} px · ${languageText("file dimensions, not spatial precision", "文件尺寸，不是空间精度")}`));
  const limits = node("div"); limits.append(node("p", "eyebrow", languageText("WHAT REMAINS UNVERIFIED", "仍然无法验证什么")), node("p", "", field(material, "limits")));
  details.append(observed, limits);
  $("clear-image").hidden = !localImage || localImage.kind !== "file";
  $("file-status").textContent = state.imageError ? languageText("The local original could not be read. Load your own copy to inspect it.", "未能读取本机原图，可以自行载入原图检查。") : localImage ? languageText("Local image only. No image is uploaded or stored by this page.", "仅本机图像预览。本页面不上传或保存图像。") : languageText("Files stay in this browser session. Nothing is uploaded or saved.", "文件仅留在当前浏览器会话中，不上传、不存储。");
  updateZoom();
}
function updateZoom() {
  const available = state.images.has(state.materialIndex) && !state.imageError;
  $("zoom").disabled = !available; $("zoom-reset").disabled = !available; $("expand-image").disabled = !available;
  $("zoom").value = state.zoom; $("zoom-value").textContent = `${state.zoom}%`;
  const image = $("material-image"); const stage = $("image-stage");
  const fittedWidth = image.naturalWidth && image.naturalHeight ? Math.min(stage.clientWidth, stage.clientHeight * image.naturalWidth / image.naturalHeight) : stage.clientWidth;
  image.style.width = `${Math.max(1, fittedWidth) * state.zoom / 100}px`;
}
function renderCases() {
  const tabs = $("case-tabs"); tabs.replaceChildren();
  state.data.cases.forEach((item, index) => {
    const button = node("button", "case-tab"); button.id = `case-tab-${index}`; button.type = "button";
    button.setAttribute("role", "tab"); button.setAttribute("aria-controls", "case-panel");
    button.setAttribute("aria-selected", index === state.caseIndex ? "true" : "false"); button.tabIndex = index === state.caseIndex ? 0 : -1;
    const copy = node("span"); copy.append(node("strong", "", field(item, "title")), node("small", "", statusLabel(item.case_status ?? "pending")));
    button.append(node("span", "case-number", item.id), copy);
    button.addEventListener("click", () => { state.caseIndex = index; renderCases(); });
    button.addEventListener("keydown", (event) => arrowTab(event, index, state.data.cases.length, (next) => { state.caseIndex = next; renderCases(); }, "case-tab-"));
    tabs.append(button);
  });
  const item = state.data.cases[state.caseIndex]; const panel = $("case-panel"); panel.replaceChildren();
  panel.setAttribute("aria-labelledby", `case-tab-${state.caseIndex}`);
  const headline = node("div", "case-headline"); headline.append(node("span", "mono", `${item.id} / ${languageText("DESIGNED PORTFOLIO QUERY", "作品集自拟查询")}`), node("span", `badge ${["source_backed_evaluation", "source_supported", "source_backed_draft", "source_backed_reframing"].includes(item.case_status) ? "supported" : "unknown"}`, statusLabel(item.case_status ?? "pending")));
  const query = node("div", "query-box"); query.append(node("span", "", languageText("QUERY", "查询词")), node("strong", "", plain(item.query)));
  panel.append(headline, node("h3", "", field(item, "title")), query, node("p", "case-label", languageText("USER INTENT", "用户意图")), node("p", "", field(item, "intent")), node("p", "case-label", languageText("CANDIDATE RECORD", "候选记录")), node("p", "", field(item, "candidate")));
  const scope = node("p", "scope", `${languageText("Relevance", "相关性")}: ${plain(item.relevance)} · ${field(item, "scope", languageText("Interpret only within the stated evidence scope.", "仅在声明的证据范围内解释。"))}`); panel.append(scope);
  const attributes = node("div", "attribute-grid");
  const names = { name: ["Name", "名称"], address: ["Address", "地址"], category: ["Category", "类别"], pin: ["Pin", "点位"], current: ["Current state", "现状"] };
  Object.entries(names).forEach(([key, pair]) => {
    const value = item.attributes?.[key]; const cell = node("div", "attribute");
    cell.append(node("span", "", languageText(...pair)), node("strong", "", plain(value)));
    if (typeof value === "object" && value) cell.append(node("small", "", field(value, "note")));
    attributes.append(cell);
  });
  panel.append(attributes, node("p", "case-label", languageText("CONCLUSION & NEXT CHECK", "结论与下一步核查")), node("p", "case-conclusion", field(item, "summary")));
  const detail = node("details"); detail.append(node("summary", "", languageText("Evidence limits and candidate provenance", "证据限制与候选来源")), node("p", "", field(item, "limitations")), node("p", "", field(item, "origin", languageText("Research record, not a captured platform result.", "研究记录，不是平台返回结果。")))); panel.append(detail);
  const links = node("div", "case-source-links"); (item.source_ids ?? []).forEach((id) => links.append(sourceLink(id)));
  const doc = node("a", "", languageText("Full case ↗", "完整案例 ↗")); doc.href = `../cases/${item.id}.md`; links.append(doc); panel.append(links);
}
function renderLedger() {
  const container = $("place-ledger"); container.replaceChildren();
  state.data.places.forEach((place) => {
    const record = node("article", "place-record"); const identity = node("div", "place-identity");
    identity.append(node("span", "mono", place.place_id), node("h3", "", place.display_name), node("p", "", languageText("Source-reported name; official name not verified.", "来源报道名称；尚未核实为官方标准名。")), node("span", "badge unknown", languageText("CURRENT LOCATION UNVERIFIED", "当前位置未核实")));
    const fields = node("dl", "record-fields");
    const coords = place.longitude == null || place.latitude == null ? languageText("null / null · no pin inferred", "null / null · 不推算点位") : `${place.longitude}, ${place.latitude} (${plain(place.crs)})`;
    const rows = [
      [languageText("Reported locality", "来源区位表述"), plain(place.reported_address)],
      [languageText("Working category", "暂定功能类别"), place.category_provisional === "community_reading_and_cultural_space" ? languageText("Community reading & cultural space", "社区阅读与文化活动空间") : plain(place.category_provisional)],
      [languageText("Longitude / latitude", "经度 / 纬度"), coords],
      [languageText("Verified aliases", "已核实别名"), place.aliases_verified?.length ? place.aliases_verified.join(" / ") : languageText("None established · not proof of no aliases", "尚未确认 · 不表示不存在别名")],
      [languageText("Source published / checked", "来源发表 / 查阅日期"), `${plain(place.source_published_on)} / ${plain(place.source_checked_on)}`],
      [languageText("Site verification date", "地点事实核验日期"), place.last_verified_on ?? languageText("null · a source read is not a site visit", "null · 读来源不等于现场核验")],
    ];
    rows.forEach(([label, value]) => { const row = node("div"); row.append(node("dt", "", label), node("dd", "", value)); fields.append(row); });
    record.append(identity, fields); container.append(record);
  });
  const issues = $("issue-summary"); issues.replaceChildren();
  state.data.issues.forEach((issue) => {
    const issueTitles = { missing_coordinates: ["Missing coordinates", "坐标缺失"], name_relation: ["Name relationship", "名称关系"], temporal_validity: ["Time validity", "时效"], category_and_address: ["Category & address", "类别与地址"], map_crs_and_rights: ["CRS & image rights", "坐标系与图像许可"] };
    const title = issueTitles[issue.topic];
    issues.append(node("span", "issue-chip", `${issue.issue_id} · ${title ? languageText(...title) : String(issue.topic ?? issue.status ?? "review")}`));
  });
}
function renderSources() {
  const container = $("source-list"); container.replaceChildren();
  state.data.sources.forEach((source) => {
    const article = node("article", "source-card"); article.id = `source-${source.source_id}`;
    const bilingual = source[`summary_${state.language}`] ?? source.summary;
    article.append(node("span", "mono", source.source_id), node("h3", "", field(source, "title", source.title)), node("p", "", plain(bilingual)));
    const dates = node("p", "source-date", `${languageText("Published", "发表")}: ${source.published_on ?? languageText("unknown", "未知")} · ${languageText("Checked", "查阅")}: ${source.checked_on ?? languageText("unknown", "未知")}`); article.append(dates);
    const details = node("details"); details.append(node("summary", "", languageText("Access, limitations & reuse", "读取状态、限制与复用")), node("p", "", `${plain(source.access_status)}. ${field(source, "limitations")} ${field(source, "reuse")}`)); article.append(details);
    if (typeof source.url === "string" && source.url.startsWith("https://")) { const a = node("a", "", languageText("Open source ↗", "查看来源 ↗")); a.href = source.url; a.target = "_blank"; a.rel = "noopener noreferrer"; article.append(a); }
    else article.append(node("p", "", languageText("Historical source metadata; originals withheld.", "仅列历史材料元数据，原件未公开。")));
    container.append(article);
  });
}
function render() {
  syncStatic(); if (!state.data) return;
  $("place-count").textContent = String(state.data.places.length).padStart(2, "0");
  $("material-count").textContent = String(state.data.materials.length).padStart(2, "0");
  $("case-count").textContent = String(state.data.cases.length).padStart(2, "0");
  renderMaterialTabs(); renderMaterial(); renderCases(); renderLedger(); renderSources();
}
async function loadData() {
  $("load-state").hidden = false; $("load-error").hidden = true; $("evidence-app").hidden = true;
  try {
    const response = await fetch("./review-data.json", { credentials: "same-origin" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (!["places", "sources", "cases", "materials", "issues"].every((key) => Array.isArray(data[key])) || !data.materials.length || !data.cases.length) throw new Error("Invalid evidence register structure");
    state.data = data;
    if (privateReview) data.materials.forEach((_, index) => { if (localPaths[index] && !state.images.has(index)) state.images.set(index, { kind: "private", url: localPaths[index] }); });
    render(); $("load-state").hidden = true; $("evidence-app").hidden = false;
  } catch (error) {
    $("load-state").hidden = true; $("load-error").hidden = false;
    $("error-detail").textContent = String(error.message || error);
  }
}
$("language").addEventListener("click", () => { state.language = state.language === "en" ? "zh" : "en"; render(); });
$("retry").addEventListener("click", loadData);
$("zoom").addEventListener("input", (event) => { state.zoom = Number(event.target.value); updateZoom(); });
$("zoom-reset").addEventListener("click", () => { state.zoom = 100; updateZoom(); $("image-stage").scrollTo(0, 0); });
$("local-image").addEventListener("change", (event) => {
  const file = event.target.files?.[0]; if (!file || !state.data) return;
  if (!["image/jpeg", "image/png", "image/webp"].includes(file.type) || file.size > 30 * 1024 * 1024) {
    $("file-status").textContent = languageText("Choose a PNG, JPEG or WebP image smaller than 30 MB.", "请选择小于30MB的PNG、JPEG或WebP图像。"); event.target.value = ""; return;
  }
  const previous = state.images.get(state.materialIndex); if (previous?.kind === "file") URL.revokeObjectURL(previous.url);
  state.images.set(state.materialIndex, { kind: "file", url: URL.createObjectURL(file) }); state.imageError = false; state.zoom = 100;
  renderMaterial(); event.target.value = "";
});
$("clear-image").addEventListener("click", () => {
  const previous = state.images.get(state.materialIndex); if (previous?.kind === "file") URL.revokeObjectURL(previous.url);
  state.images.delete(state.materialIndex); state.imageError = false; renderMaterial();
});
$("material-image").addEventListener("error", () => { if (state.data && $("material-image").getAttribute("src")) { state.imageError = true; renderMaterial(); } });
$("material-image").addEventListener("load", updateZoom);
window.addEventListener("resize", updateZoom);
$("expand-image").addEventListener("click", () => {
  const source = state.images.get(state.materialIndex); if (!source || state.imageError) return;
  $("expanded-image").src = source.url; $("expanded-image").alt = $("material-image").alt;
  $("dialog-title").textContent = field(state.data.materials[state.materialIndex], "title"); $("image-dialog").showModal();
});
$("close-dialog").addEventListener("click", () => $("image-dialog").close());
window.addEventListener("beforeunload", () => state.images.forEach((image) => { if (image.kind === "file") URL.revokeObjectURL(image.url); }));
loadData();
