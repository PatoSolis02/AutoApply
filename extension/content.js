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
    "h1"
  ]);

  const company = textFromSelectors([
    ".job-details-jobs-unified-top-card__company-name a",
    ".job-details-jobs-unified-top-card__company-name",
    ".jobs-unified-top-card__company-name a",
    ".jobs-unified-top-card__company-name"
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

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "EXTRACT_JOB") {
    return;
  }

  const data = extractJobDetails();
  const valid = Boolean(data.title && data.company && data.job_url && data.description_raw);

  if (!valid) {
    sendResponse({
      ok: false,
      error: "Could not extract all required fields. Open a specific job detail in the right panel and try again."
    });
    return;
  }

  sendResponse({ ok: true, data });
});
