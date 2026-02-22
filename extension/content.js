function textFromSelectors(selectors) {
  for (const selector of selectors) {
    const el = document.querySelector(selector);
    if (el && el.textContent) {
      const value = compact(el.textContent);
      if (value) {
        return value;
      }
    }
  }
  return null;
}

function canonicalJobUrl() {
  const url = new URL(window.location.href);
  const currentJobId = url.searchParams.get("currentJobId");
  if (currentJobId) {
    return `https://www.linkedin.com/jobs/view/${currentJobId}`;
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

function fallbackCompanyFromDocumentTitle() {
  const title = compact(document.title.replace(/\s*\|\s*LinkedIn\s*$/, ""));
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

function fallbackCompanyFromTopCard() {
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

  return "";
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
  if (targeted && targeted.length >= 80) {
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
      if (candidate.length >= 80) {
        return candidate;
      }
    }
  }

  return text.length >= 160 ? text : "";
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

  return text.length >= 300 ? text.slice(0, 3000) : "";
}

function extractJobDetails() {
  const jsonLd = extractFromJsonLd();

  const title = textFromSelectors([
    ".job-details-jobs-unified-top-card__job-title h1",
    ".job-details-jobs-unified-top-card__job-title",
    ".jobs-unified-top-card__job-title h1",
    ".jobs-unified-top-card__job-title",
    "[data-test-job-title]",
    "h1"
  ]);

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

  const location = textFromSelectors([
    ".job-details-jobs-unified-top-card__primary-description-container .tvm__text",
    ".job-details-jobs-unified-top-card__primary-description-container span",
    ".jobs-unified-top-card__bullet",
    ".jobs-unified-top-card__subtitle-primary-grouping",
    ".jobs-unified-top-card__primary-description"
  ]);

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
    title: title || document.title.replace(/\s*\|\s*LinkedIn\s*$/, "").trim(),
    company:
      sanitizeCompanyName(company)
      || fallbackCompanyFromTopCard()
      || jsonLd.company
      || fallbackCompanyFromDocumentTitle(),
    location,
    job_url: canonicalJobUrl(),
    description_raw:
      descriptionRaw
      || jsonLd.description
      || fallbackDescriptionFromPanel()
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
