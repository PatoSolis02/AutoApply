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

function findActiveJobCard() {
  return document.querySelector(".jobs-search-results__list-item--active")
    || document.querySelector(".jobs-search-results-list__list-item--active")
    || document.querySelector(".job-card-container--clickable[aria-current='true']")
    || document.querySelector("li.jobs-search-results__list-item[aria-current='true']");
}

function activeCardJobUrl(activeCard) {
  if (!activeCard) return "";
  const link = activeCard.querySelector("a[href*='/jobs/view/']");
  if (!link) return "";
  const href = link.getAttribute("href");
  if (!href) return "";
  try {
    return new URL(href, window.location.origin).href;
  } catch (_error) {
    return "";
  }
}

function canonicalJobUrl(activeCard = null) {
  const url = new URL(window.location.href);
  const currentJobId = url.searchParams.get("currentJobId");
  if (currentJobId) {
    return `https://www.linkedin.com/jobs/view/${currentJobId}`;
  }
  const fromCard = activeCardJobUrl(activeCard);
  if (fromCard && !/\/jobs\/view\//i.test(url.pathname)) {
    return fromCard;
  }
  return url.href;
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

function fallbackTitleFromDocumentTitle() {
  const cleaned = compact(document.title.replace(/\s*\|\s*LinkedIn\s*$/i, ""));
  if (!cleaned) return "";

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

function extractFromJsonLd() {
  const scripts = Array.from(document.querySelectorAll("script[type='application/ld+json']"));
  const best = { company: "", description: "" };

  for (const script of scripts) {
    const raw = script.textContent;
    if (!raw) continue;

    try {
      const parsed = JSON.parse(raw);
      const posting = findJobPostingNode(parsed);
      if (!posting) continue;

      const company =
        sanitizeCompanyName(posting?.hiringOrganization?.name)
        || sanitizeCompanyName(posting?.hiringOrganization?.legalName)
        || sanitizeCompanyName(posting?.employerOverview?.name)
        || "";

      const description = htmlToText(posting?.description || posting?.jobDescription || "");

      if (company && !best.company) {
        best.company = company;
      }
      if (description && description.length > best.description.length) {
        best.description = description;
      }
    } catch (_error) {
      continue;
    }
  }

  return best;
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
    ".jobs-unified-top-card__primary-description span",
    ".jobs-unified-top-card__primary-description",
  ];
  for (const selector of selectors) {
    const matches = Array.from(document.querySelectorAll(selector));
    for (const match of matches) {
      const value = compact(match.textContent || "");
      if (!value) continue;
      if (company && value.toLowerCase() === company.toLowerCase()) continue;
      if (looksLikeJobMeta(value)) continue;
      if (!looksLikeLocation(value)) continue;
      return value;
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
  if (direct && direct.length >= 40) {
    return direct;
  }

  const insightNodes = Array.from(
    activeCard.querySelectorAll(".job-card-container__job-insight, .job-card-container__footer-item")
  );
  if (insightNodes.length === 0) {
    return "";
  }
  const combined = compact(insightNodes.map((node) => readText(node)).filter(Boolean).join(" "));
  return combined.length >= 60 ? combined : "";
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
  if (targeted && targeted.length >= 60) {
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
      if (candidate.length >= 60) {
        return candidate;
      }
    }
  }

  return text.length >= 120 ? text : "";
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
  return asText.length >= 40 ? asText : "";
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

  return text.length >= 120 ? text.slice(0, 3000) : "";
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
  ]) || fallbackTitleFromActiveCard(activeCard) || fallbackTitleFromDocumentTitle();

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
    job_url: canonicalJobUrl(activeCard),
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

  extractJobDetailsWithWait().then(({ data, missing }) => {
    if (missing.length > 0) {
      sendResponse({
        ok: false,
        error: `Could not extract required fields (${missing.join(", ")}). Open a specific job detail in the right panel and try again.`
      });
      return;
    }

    sendResponse({ ok: true, data });
  });

  return true;
});
