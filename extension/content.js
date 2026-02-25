function textFromSelectors(selectors, root = document) {
  for (const selector of selectors) {
    const el = root.querySelector(selector);
    if (el && el.textContent) {
      const value = compact(el.textContent);
      if (value) {
        return value;
      }
    }
  }
  return null;
}

function readDataAttribute(el, name) {
  if (!el || typeof el.getAttribute !== "function") return "";
  return compact(el.getAttribute(name) || "");
}

function extractJobIdFromUrlLike(value) {
  if (value === null || value === undefined) return "";
  const raw = compact(String(value));
  if (!raw) return "";
  if (/^\d{4,}$/.test(raw)) return raw;

  const fromPath = raw.match(/\/jobs\/view\/(\d{4,})/i);
  if (fromPath?.[1]) {
    return fromPath[1];
  }

  const fromQuery = raw.match(/[?&]currentJobId=(\d{4,})\b/i);
  if (fromQuery?.[1]) {
    return fromQuery[1];
  }

  const fromUrn = raw.match(/jobPosting:(\d{4,})/i);
  if (fromUrn?.[1]) {
    return fromUrn[1];
  }

  return "";
}

function canonicalLinkedInJobUrl(jobId) {
  return jobId ? `https://www.linkedin.com/jobs/view/${jobId}` : "";
}

function findActiveJobCard() {
  return document.querySelector(".jobs-search-results__list-item--active")
    || document.querySelector(".jobs-search-results-list__list-item--active")
    || document.querySelector(".job-card-container--clickable[aria-current='true']")
    || document.querySelector("li.jobs-search-results__list-item[aria-current='true']");
}

function activeCardJobUrl(activeCard) {
  if (!activeCard) return "";
  const link = activeCard.querySelector("a[href*='/jobs/']");
  if (!link) return "";
  const href = link.getAttribute("href");
  if (!href) return "";

  const fromHrefId = extractJobIdFromUrlLike(href);
  if (fromHrefId) {
    if (/\/jobs\/view\//i.test(href)) {
      try {
        return new URL(href, window.location.origin).href;
      } catch (_error) {
        return canonicalLinkedInJobUrl(fromHrefId);
      }
    }
    return canonicalLinkedInJobUrl(fromHrefId);
  }

  try {
    return new URL(href, window.location.origin).href;
  } catch (_error) {
    return "";
  }
}

function activeCardJobId(activeCard) {
  if (!activeCard) return "";

  const dataCandidates = [
    readDataAttribute(activeCard, "data-occludable-job-id"),
    readDataAttribute(activeCard, "data-job-id"),
    readDataAttribute(activeCard, "data-id"),
    readDataAttribute(activeCard, "data-entity-urn"),
  ];
  for (const candidate of dataCandidates) {
    const id = extractJobIdFromUrlLike(candidate);
    if (id) return id;
  }

  const anchor = activeCard.querySelector("a[href*='/jobs/']");
  const href = compact(anchor?.getAttribute("href") || "");
  return extractJobIdFromUrlLike(href);
}

function canonicalJobUrl(activeCard = null, jsonLdJobUrl = "") {
  const fromCurrentUrl = extractJobIdFromUrlLike(window.location.href);
  if (fromCurrentUrl) {
    return canonicalLinkedInJobUrl(fromCurrentUrl);
  }

  const fromActiveCardId = activeCardJobId(activeCard);
  if (fromActiveCardId) {
    return canonicalLinkedInJobUrl(fromActiveCardId);
  }

  const fromCard = activeCardJobUrl(activeCard);
  if (fromCard) {
    return fromCard;
  }

  const fromJsonLd = extractJobIdFromUrlLike(jsonLdJobUrl);
  if (fromJsonLd) {
    return canonicalLinkedInJobUrl(fromJsonLd);
  }

  return window.location.href;
}

function compact(text) {
  return (text || "").replace(/\s+/g, " ").trim();
}

function sanitizeCompanyName(value) {
  const candidate = compact(value).replace(/\s+\|.*$/, "");
  if (!candidate) return "";
  if (candidate.length > 120) return "";
  if (/^\d+\+?\s+applicants?/i.test(candidate)) return "";
  if (/^(easy apply|promoted|actively reviewing)$/i.test(candidate)) return "";
  return candidate;
}

function titleFromCandidate(value) {
  const cleaned = compact((value || "").replace(/\s*\|\s*LinkedIn\s*$/i, ""));
  if (!cleaned) return "";
  if (/^linkedin$/i.test(cleaned)) return "";

  const atMatch = cleaned.match(/^(.*?)\s+at\s+.+$/i);
  if (atMatch?.[1]) {
    return compact(atMatch[1]);
  }

  const parts = cleaned.split(" - ").map((part) => compact(part)).filter(Boolean);
  if (parts.length >= 2) {
    return parts[0];
  }

  return cleaned;
}

function fallbackTitleFromDocumentTitle() {
  return titleFromCandidate(document.title);
}

function fallbackTitleFromMeta() {
  const metaTitle = compact(
    document.querySelector("meta[property='og:title']")?.getAttribute("content")
      || document.querySelector("meta[name='title']")?.getAttribute("content")
      || ""
  );
  return titleFromCandidate(metaTitle);
}

function fallbackCompanyFromDocumentTitle() {
  const title = compact(document.title.replace(/\s*\|\s*LinkedIn\s*$/i, ""));
  if (!title) return "";

  const atMatch = title.match(/\bat\s+(.+)$/i);
  if (atMatch?.[1]) {
    return sanitizeCompanyName(atMatch[1]);
  }

  const parts = title.split(" - ").map((part) => compact(part)).filter(Boolean);
  if (parts.length >= 2) {
    return sanitizeCompanyName(parts[parts.length - 1]);
  }

  return "";
}

function readText(el) {
  if (!el) return "";
  return compact(el.innerText || el.textContent || "");
}

function htmlToText(html) {
  if (!html) return "";
  const node = document.createElement("div");
  node.innerHTML = html;
  return readText(node);
}

function looksLikeLocation(value) {
  const candidate = compact(value);
  if (!candidate) return false;
  if (/\b(remote|hybrid|on-site|onsite)\b/i.test(candidate)) return true;
  if (/,\s*[A-Z]{2}\b/.test(candidate)) return true;
  if (/\b(united states|usa|canada|uk|india|germany|france|spain)\b/i.test(candidate)) return true;
  return false;
}

function looksLikeJobMeta(value) {
  const candidate = compact(value);
  if (!candidate) return false;
  return /^\d+\+?\s+applicants?/i.test(candidate)
    || /^\d+\s+(hour|day|week|month)s?\s+ago$/i.test(candidate)
    || /^(easy apply|promoted|reposted)$/i.test(candidate);
}

function isJobPostingType(typeValue) {
  if (typeof typeValue === "string") {
    return typeValue.toLowerCase() === "jobposting";
  }
  if (Array.isArray(typeValue)) {
    return typeValue.some((entry) => typeof entry === "string" && entry.toLowerCase() === "jobposting");
  }
  return false;
}

function findJobPostingNode(node) {
  if (!node) return null;
  if (Array.isArray(node)) {
    for (const entry of node) {
      const found = findJobPostingNode(entry);
      if (found) return found;
    }
    return null;
  }
  if (typeof node !== "object") return null;
  if (isJobPostingType(node["@type"])) return node;
  if (Array.isArray(node["@graph"])) return findJobPostingNode(node["@graph"]);
  return null;
}

function collectJobPostingNodes(node, into = []) {
  if (!node) return into;
  if (Array.isArray(node)) {
    for (const entry of node) {
      collectJobPostingNodes(entry, into);
    }
    return into;
  }
  if (typeof node !== "object") return into;
  if (isJobPostingType(node["@type"])) {
    into.push(node);
  }
  if (Array.isArray(node["@graph"])) {
    collectJobPostingNodes(node["@graph"], into);
  }
  return into;
}

function companyFromJsonLdPosting(posting) {
  const organization = posting?.hiringOrganization;
  const candidates = [];

  if (typeof organization === "string") {
    candidates.push(organization);
  } else if (Array.isArray(organization)) {
    for (const item of organization) {
      if (typeof item === "string") {
        candidates.push(item);
      } else if (item && typeof item === "object") {
        candidates.push(item.name, item.legalName);
      }
    }
  } else if (organization && typeof organization === "object") {
    candidates.push(organization.name, organization.legalName);
  }

  candidates.push(posting?.employerOverview?.name);

  for (const candidate of candidates) {
    const company = sanitizeCompanyName(candidate);
    if (company) return company;
  }

  return "";
}

function locationFromJsonLdPosting(posting) {
  const locationNodes = Array.isArray(posting?.jobLocation)
    ? posting.jobLocation
    : posting?.jobLocation
      ? [posting.jobLocation]
      : [];

  for (const node of locationNodes) {
    if (!node || typeof node !== "object") continue;
    const address = node.address && typeof node.address === "object" ? node.address : node;
    const locality = compact(address.addressLocality || "");
    const region = compact(address.addressRegion || "");
    const country = compact(address.addressCountry || "");

    const withRegion = [locality, region].filter(Boolean).join(", ");
    if (looksLikeLocation(withRegion)) return withRegion;
    if (looksLikeLocation(locality)) return locality;
    if (looksLikeLocation(country)) return country;
  }

  const remoteHint = compact(posting?.jobLocationType || posting?.workLocationRequirements || "");
  if (/telecommute|remote/i.test(remoteHint)) {
    return "Remote";
  }

  return "";
}

function descriptionFromJsonLdPosting(posting) {
  return htmlToText(posting?.description || posting?.jobDescription || "");
}

function titleFromJsonLdPosting(posting) {
  return compact(posting?.title || posting?.name || "");
}

function identifierFromJsonLdPosting(posting) {
  const identifier = posting?.identifier;
  if (typeof identifier === "string") {
    return extractJobIdFromUrlLike(identifier);
  }
  if (identifier && typeof identifier === "object") {
    return extractJobIdFromUrlLike(identifier.value || identifier.name || "");
  }
  return "";
}

function scoreJsonLdPosting(posting, currentJobId) {
  const jobId = identifierFromJsonLdPosting(posting) || extractJobIdFromUrlLike(posting?.url || posting?.mainEntityOfPage || "");
  const company = companyFromJsonLdPosting(posting);
  const title = titleFromJsonLdPosting(posting);
  const description = descriptionFromJsonLdPosting(posting);

  let score = 0;
  if (currentJobId && jobId && currentJobId === jobId) {
    score += 100;
  }
  if (description.length >= 80) {
    score += 10;
  } else if (description.length >= 40) {
    score += 5;
  }
  if (company) score += 3;
  if (title) score += 2;
  if (jobId) score += 1;
  return score;
}

function extractFromJsonLd() {
  const scripts = Array.from(document.querySelectorAll("script[type='application/ld+json']"));
  const currentJobId = extractJobIdFromUrlLike(window.location.href);
  const best = { title: "", company: "", description: "", location: "", job_url: "", score: -1 };

  for (const script of scripts) {
    const raw = script.textContent;
    if (!raw) continue;

    try {
      const parsed = JSON.parse(raw);
      const postings = collectJobPostingNodes(parsed);
      if (postings.length === 0) {
        const one = findJobPostingNode(parsed);
        if (one) postings.push(one);
      }
      if (postings.length === 0) continue;

      for (const posting of postings) {
        const score = scoreJsonLdPosting(posting, currentJobId);
        if (score < best.score) continue;

        best.title = titleFromJsonLdPosting(posting);
        best.company = companyFromJsonLdPosting(posting);
        best.description = descriptionFromJsonLdPosting(posting);
        best.location = locationFromJsonLdPosting(posting);
        best.job_url = compact(posting?.url || posting?.mainEntityOfPage || "");
        best.score = score;
      }
    } catch (_error) {
      continue;
    }
  }

  return {
    title: best.title,
    company: best.company,
    description: best.description,
    location: best.location,
    job_url: best.job_url,
  };
}

function fallbackCompanyFromTopCard(knownTitle = "") {
  const topCard = document.querySelector(".jobs-unified-top-card")
    || document.querySelector(".job-details-jobs-unified-top-card__container")
    || document.querySelector(".job-details-jobs-unified-top-card");
  if (!topCard || !topCard.textContent) return "";

  const companyAnchor = topCard.querySelector("a[href*='/company/']");
  if (companyAnchor && companyAnchor.textContent) {
    return sanitizeCompanyName(companyAnchor.textContent);
  }

  const lines = topCard.innerText
    .split("\n")
    .map((line) => compact(line))
    .filter(Boolean);

  for (const line of lines) {
    if (line.includes("·")) {
      const maybeCompany = compact(line.split("·")[0]);
      if (maybeCompany && !/\d/.test(maybeCompany)) {
        return sanitizeCompanyName(maybeCompany);
      }
    }
  }

  for (const line of lines) {
    const candidate = sanitizeCompanyName(line);
    if (!candidate) continue;
    if (knownTitle && candidate.toLowerCase() === knownTitle.toLowerCase()) continue;
    if (looksLikeLocation(candidate)) continue;
    if (looksLikeJobMeta(candidate)) continue;
    return candidate;
  }

  return "";
}

function fallbackCompanyFromActiveCard(activeCard) {
  if (!activeCard) return "";

  const fromSelectors = textFromSelectors([
    ".job-card-container__company-name",
    ".artdeco-entity-lockup__subtitle span",
    "a[href*='/company/']",
  ], activeCard);
  return sanitizeCompanyName(fromSelectors || "");
}

function fallbackTitleFromActiveCard(activeCard) {
  if (!activeCard) return "";
  return textFromSelectors([
    ".job-card-list__title",
    ".job-card-list__title--link",
    ".job-card-container__link",
    "a[href*='/jobs/view/']",
  ], activeCard) || "";
}

function fallbackLocationFromActiveCard(activeCard, company = "") {
  if (!activeCard) return "";
  const selectors = [
    ".job-card-container__metadata-item",
    ".job-card-container__metadata-wrapper li",
    ".job-card-container__job-insight",
    ".job-card-container__footer-item",
  ];

  for (const selector of selectors) {
    const matches = Array.from(activeCard.querySelectorAll(selector));
    for (const match of matches) {
      const value = compact(match.textContent || "");
      if (!value) continue;
      if (company && value.toLowerCase() === company.toLowerCase()) continue;
      if (!looksLikeLocation(value)) continue;
      return value;
    }
  }

  return "";
}

function locationFromTopCard(company = "") {
  const selectors = [
    ".job-details-jobs-unified-top-card__primary-description-container .tvm__text",
    ".job-details-jobs-unified-top-card__primary-description-container span",
    ".jobs-unified-top-card__bullet",
    ".jobs-unified-top-card__subtitle-primary-grouping span",
    ".jobs-unified-top-card__primary-description-without-tagline",
    ".jobs-unified-top-card__primary-description span",
    ".jobs-unified-top-card__primary-description",
  ];
  for (const selector of selectors) {
    const matches = Array.from(document.querySelectorAll(selector));
    for (const match of matches) {
      const value = compact(match.textContent || "");
      if (!value) continue;
      const segments = value.includes("·")
        ? value.split("·").map((segment) => compact(segment)).filter(Boolean)
        : [value];
      for (const segment of segments) {
        if (!segment) continue;
        if (company && segment.toLowerCase() === company.toLowerCase()) continue;
        if (looksLikeJobMeta(segment)) continue;
        if (!looksLikeLocation(segment)) continue;
        return segment;
      }
    }
  }
  return "";
}

function fallbackDescriptionFromActiveCard(activeCard) {
  if (!activeCard) return "";

  const direct = textFromSelectors([
    ".job-card-list__description",
    ".job-card-container__description",
    "[class*='job-card-list__description']",
  ], activeCard);
  if (direct && direct.length >= 20) {
    return direct;
  }

  const insightNodes = Array.from(
    activeCard.querySelectorAll(".job-card-container__job-insight, .job-card-container__footer-item")
  );
  if (insightNodes.length === 0) {
    return "";
  }
  const combined = compact(insightNodes.map((node) => readText(node)).filter(Boolean).join(" "));
  return combined.length >= 40 ? combined : "";
}

function fallbackDescriptionFromPanel() {
  const panel = document.querySelector(".jobs-search__job-details--container")
    || document.querySelector(".jobs-search-two-pane__job-details")
    || document.querySelector(".jobs-details")
    || document.querySelector(".job-view-layout");
  if (!panel || !panel.textContent) return "";

  const targeted = textFromSelectors([
    ".jobs-description-content__text",
    ".jobs-description-content__text--stretch",
    ".jobs-box__html-content",
    ".job-details-about-the-job-module__description",
    "[data-test-job-description]",
    "[class*='show-more-less-html__markup']",
    "[class*='jobs-description-content']",
  ]);
  if (targeted && targeted.length >= 40) {
    return targeted;
  }

  const text = compact(panel.innerText);
  if (!text) return "";

  const lowered = text.toLowerCase();
  const anchors = ["about the job", "job description", "about this role", "responsibilities"];

  for (const anchor of anchors) {
    const index = lowered.indexOf(anchor);
    if (index >= 0) {
      const candidate = compact(text.slice(index));
      if (candidate.length >= 40) {
        return candidate;
      }
    }
  }

  return text.length >= 80 ? text : "";
}

function fallbackDescriptionFromMeta() {
  const candidates = [
    "meta[property='og:description']",
    "meta[name='description']",
  ];
  let content = "";
  for (const selector of candidates) {
    const el = document.querySelector(selector);
    const value = compact(el?.getAttribute("content") || "");
    if (value) {
      content = value;
      break;
    }
  }
  if (!content) return "";
  const asText = htmlToText(content);
  return asText.length >= 25 ? asText : "";
}

function fallbackDescriptionFromPage() {
  const body = document.body;
  if (!body) return "";

  const text = compact(body.innerText || "");
  if (!text) return "";

  const lowered = text.toLowerCase();
  const aboutIndex = lowered.indexOf("about the job");
  if (aboutIndex >= 0) {
    return compact(text.slice(aboutIndex, Math.min(text.length, aboutIndex + 5000)));
  }

  const descriptionIndex = lowered.indexOf("job description");
  if (descriptionIndex >= 0) {
    return compact(text.slice(descriptionIndex, Math.min(text.length, descriptionIndex + 5000)));
  }

  return text.length >= 80 ? text.slice(0, 3000) : "";
}

function extractJobDetails() {
  const jsonLd = extractFromJsonLd();
  const activeCard = findActiveJobCard();

  const title = textFromSelectors([
    ".job-details-jobs-unified-top-card__job-title h1",
    ".job-details-jobs-unified-top-card__job-title",
    ".jobs-unified-top-card__job-title h1",
    ".jobs-unified-top-card__job-title",
    "[data-test-job-title]",
    "h1"
  ]) || fallbackTitleFromActiveCard(activeCard) || fallbackTitleFromDocumentTitle() || fallbackTitleFromMeta() || jsonLd.title;

  const company = textFromSelectors([
    ".job-details-jobs-unified-top-card__company-name a",
    ".job-details-jobs-unified-top-card__company-name",
    ".job-details-jobs-unified-top-card__company-name-link",
    ".jobs-unified-top-card__company-name a",
    ".jobs-unified-top-card__company-name",
    ".job-details-jobs-unified-top-card__primary-description a[href*='/company/']",
    ".jobs-unified-top-card__primary-description-without-tagline a[href*='/company/']",
    ".jobs-unified-top-card__subtitle-primary-grouping a[href*='/company/']",
    ".jobs-unified-top-card__subtitle-container a[href*='/company/']",
    "[data-test-id='job-details-company-name']",
    ".jobs-details-top-card__company-url",
    "[class*='top-card'] a[href*='/company/']",
    "a[href*='/company/'] span",
    "a[href*='/company/']"
  ]);
  const normalizedCompany =
    sanitizeCompanyName(company)
    || fallbackCompanyFromTopCard(title)
    || fallbackCompanyFromActiveCard(activeCard)
    || jsonLd.company
    || fallbackCompanyFromDocumentTitle();
  const location =
    locationFromTopCard(normalizedCompany)
    || fallbackLocationFromActiveCard(activeCard, normalizedCompany)
    || jsonLd.location
    || null;

  const descriptionNode = document.querySelector("#job-details")
    || document.querySelector(".jobs-description-content__text")
    || document.querySelector(".jobs-description-content__text--stretch")
    || document.querySelector(".jobs-description__content")
    || document.querySelector(".jobs-box__html-content")
    || document.querySelector(".job-details-about-the-job-module__description")
    || document.querySelector("[class*='show-more-less-html__markup']")
    || document.querySelector("[class*='jobs-description-content']")
    || document.querySelector(".jobs-description")
    || document.querySelector("[data-test-job-description]");
  const descriptionRaw = descriptionNode ? compact(descriptionNode.innerText) : "";

  return {
    title,
    company: normalizedCompany,
    location,
    job_url: canonicalJobUrl(activeCard, jsonLd.job_url),
    description_raw:
      descriptionRaw
      || jsonLd.description
      || fallbackDescriptionFromPanel()
      || fallbackDescriptionFromActiveCard(activeCard)
      || fallbackDescriptionFromMeta()
      || fallbackDescriptionFromPage()
  };
}

function missingFields(data) {
  const missing = [];
  if (!data.title) missing.push("title");
  if (!data.company) missing.push("company");
  if (!data.description_raw) missing.push("description");
  if (!data.job_url) missing.push("job_url");
  return missing;
}

function recoveryGuidanceForField(field) {
  if (field === "title") {
    return "click the target role so the right-side detail panel shows the job title";
  }
  if (field === "company") {
    return "wait for company metadata near the title or open the company-linked posting view";
  }
  if (field === "description") {
    return "scroll/expand the description section (About the job) before capturing";
  }
  if (field === "job_url") {
    return "open a specific LinkedIn job detail (jobs/view) before retrying";
  }
  return "refresh the page and retry";
}

function buildMissingFieldError(missing) {
  const detail = missing
    .map((field) => `${field}: ${recoveryGuidanceForField(field)}`)
    .join(" | ");
  return `Could not extract required fields (${missing.join(", ")}). Recovery: ${detail}. If this keeps failing, use AutoApply manual capture form with copied job details.`;
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function extractJobDetailsWithWait(timeoutMs = 9000, intervalMs = 300) {
  const started = Date.now();
  let data = extractJobDetails();
  let missing = missingFields(data);

  while (missing.length > 0 && Date.now() - started < timeoutMs) {
    await wait(intervalMs);
    data = extractJobDetails();
    missing = missingFields(data);
  }

  return { data, missing };
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "EXTRACT_JOB") {
    return;
  }

  const timeoutMs =
    typeof message?.timeoutMs === "number" && Number.isFinite(message.timeoutMs)
      ? Math.max(0, message.timeoutMs)
      : 9000;
  const intervalMs =
    typeof message?.intervalMs === "number" && Number.isFinite(message.intervalMs)
      ? Math.max(10, message.intervalMs)
      : 300;

  extractJobDetailsWithWait(timeoutMs, intervalMs).then(({ data, missing }) => {
    if (missing.length > 0) {
      sendResponse({
        ok: false,
        error: buildMissingFieldError(missing)
      });
      return;
    }

    sendResponse({ ok: true, data });
  });

  return true;
});
