function textFromSelectors(selectors) {
  for (const selector of selectors) {
    const el = document.querySelector(selector);
    if (el && el.textContent) {
      const value = el.textContent.trim();
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

function fallbackCompanyFromTopCard() {
  const topCard = document.querySelector(".jobs-unified-top-card")
    || document.querySelector(".job-details-jobs-unified-top-card__container")
    || document.querySelector(".job-details-jobs-unified-top-card");
  if (!topCard || !topCard.textContent) return "";

  const companyAnchor = topCard.querySelector("a[href*='/company/']");
  if (companyAnchor && companyAnchor.textContent) {
    return compact(companyAnchor.textContent);
  }

  const lines = topCard.innerText
    .split("\n")
    .map((line) => compact(line))
    .filter(Boolean);

  for (const line of lines) {
    if (line.includes("·")) {
      const maybeCompany = compact(line.split("·")[0]);
      if (maybeCompany && !/\d/.test(maybeCompany)) {
        return maybeCompany;
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

  const text = compact(panel.innerText);
  if (!text) return "";

  const aboutIndex = text.toLowerCase().indexOf("about the job");
  const candidate = aboutIndex >= 0 ? text.slice(aboutIndex) : text;

  // Avoid tiny fragments from loading placeholders.
  return candidate.length >= 120 ? candidate : "";
}

function extractJobDetails() {
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
    ".jobs-unified-top-card__primary-description-without-tagline a[href*='/company/']",
    ".jobs-unified-top-card__subtitle-primary-grouping a[href*='/company/']",
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
    || document.querySelector(".jobs-description")
    || document.querySelector("[data-test-job-description]");
  const descriptionRaw = descriptionNode
    ? compact(descriptionNode.innerText)
    : fallbackDescriptionFromPanel();

  return {
    title: title || document.title.replace(/\s*\|\s*LinkedIn\s*$/, "").trim(),
    company: company || fallbackCompanyFromTopCard(),
    location,
    job_url: canonicalJobUrl(),
    description_raw: descriptionRaw
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
