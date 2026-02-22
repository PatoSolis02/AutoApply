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
    ".jobs-unified-top-card__company-name a",
    ".jobs-unified-top-card__company-name",
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
    || document.querySelector(".jobs-box__html-content")
    || document.querySelector(".jobs-description")
    || document.querySelector("[data-test-job-description]");
  const descriptionRaw = descriptionNode ? descriptionNode.innerText.trim() : "";

  return {
    title: title || document.title.replace(/\s*\|\s*LinkedIn\s*$/, "").trim(),
    company: company || "",
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

async function extractJobDetailsWithWait(timeoutMs = 5000, intervalMs = 250) {
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
