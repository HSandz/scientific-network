/**
 * Display names. Data keeps the extracted surface form; the interface shows sentence case
 * for methods, tasks and topics ("Large language models", not "Large Language Models (LLMs)"),
 * keeps proper names (datasets, organizations, people) as written, and never shows raw IDs.
 */

const KEEP_WORD = /^(?:[A-Z0-9]{2,}s?|.*[a-z][A-Z].*|.*\d.*|[A-Z]\.?|[A-Z][a-z]*-[A-Z].*)$/;

const PROPER = new Set(
  "Gaussian Bayesian Markov Monte Carlo Laplacian Euclidean Hilbert Wasserstein Shapley Nash Boolean Hamiltonian Lipschitz Kalman Fourier Langevin Hessian Riemannian Poisson Dirichlet Gibbs Turing Pareto Stackelberg English Chinese Wikipedia Internet Atari Minecraft StarCraft Transformer".split(" "),
);

function sentenceCase(name: string): string {
  const words = name.split(/\s+/);
  return words
    .map((w, i) => {
      if (KEEP_WORD.test(w) || PROPER.has(w)) return w;
      if (i === 0) return w.charAt(0).toUpperCase() + w.slice(1);
      // Title-case words become lower case; already-lower words stay.
      return /^[A-Z][a-z'’]+$/.test(w) ? w.toLowerCase() : w;
    })
    .join(" ");
}

/** "Large Language Models (LLMs)" → "Large language models". */
export function subjectName(name: string | null | undefined, kind?: string | null): string {
  if (!name) return "";
  let n = name.trim().replace(/\s+/g, " ");
  if (kind === "Dataset") return n.charAt(0).toUpperCase() + n.slice(1);
  n = n.replace(/\s*\((?:[A-Z][A-Za-z0-9-]*s?)\)\s*$/, "");
  return sentenceCase(n);
}

const COUNTRY_SUFFIX = /\s\((?:United States|China|United Kingdom|Germany|France|Japan|Canada|Australia|Singapore|India|South Korea|Hong Kong|Switzerland|Netherlands|Israel)\)$/;

export function orgName(name: string | null | undefined): string {
  if (!name) return "";
  return name.replace(COUNTRY_SUFFIX, "").trim();
}

/** Short form for tight graph labels; the full name stays in the tooltip. */
export function shortOrg(name: string): string {
  return orgName(name)
    .replace("Beijing National Research Center for Information Science and Technology", "Beijing National Research Center (BNRist)")
    .replace("The Hong Kong University of Science and Technology (Guangzhou)", "HKUST (Guangzhou)")
    .replace("The Hong Kong University of Science and Technology", "HKUST")
    .replace("Beijing University of Posts and Telecommunications", "Beijing Univ. of Posts and Telecom.")
    .replace("University of Science and Technology of China", "Univ. of Science and Technology of China")
    .replace("Shanghai Artificial Intelligence Laboratory", "Shanghai AI Laboratory")
    .replace("Chinese Academy of Sciences", "CAS");
}

export function displayName(name: string | null | undefined, label?: string | null): string {
  if (!name) return "";
  if (label === "Method" || label === "Task" || label === "Topic" || label === "Dataset") return subjectName(name, label);
  if (label === "Organization") return orgName(name);
  return name;
}

export function kindFromId(id: string | null | undefined): string | null {
  if (!id) return null;
  const head = id.split(":")[0];
  return (
    {
      method: "Method",
      task: "Task",
      dataset: "Dataset",
      topic: "Topic",
      organization: "Organization",
      researcher: "Researcher",
      paper: "Paper",
      venue: "Venue",
      community: "Community",
    } as Record<string, string>
  )[head] || null;
}

export function plural(n: number, one: string, many = `${one}s`): string {
  return `${n.toLocaleString("en")} ${n === 1 ? one : many}`;
}

export function truncate(s: string, n: number): string {
  return s.length > n ? `${s.slice(0, n - 1).trimEnd()}…` : s;
}

/**
 * Readable title for a generated community report: drops internal ids such as "Community
 * research:L1:4:" or "Research community L0:90 focuses on". Returns "" when nothing readable
 * is left, so the caller can fall back to the community's top terms.
 */
export function communityTitle(title: string | null | undefined): string {
  let t = (title || "").replace(/\*\*/g, "").trim();
  const id = String.raw`(?:research:)?(?:L0|L1|N1|N2):\d+(?::\d+)?`;
  t = t.replace(new RegExp(String.raw`^(?:the\s+)?(?:research\s+)?community\s+${id}\s*(?::|-|–)?\s*`, "i"), "");
  t = t.replace(/^(?:(?:primarily|mainly)\s+)?(?:focus(?:es|ed|ing)?\s+on|centers?\s+on|dominates?|is\s+about)\s+/i, "");
  t = t.replace(new RegExp(String.raw`\s*\b(?:in|of|for)\s+(?:(?:research\s+)?community\s+)?${id}`, "gi"), "");
  t = t.replace(new RegExp(String.raw`\(?\b(?:(?:research\s+)?community\s+)?${id}\b\)?`, "gi"), "");
  t = t.replace(/\s{2,}/g, " ").replace(/^[\s:–-]+|[\s:–.-]+$/g, "");
  if (t.length < 4 || /^(?:research\s+)?community$/i.test(t)) return "";
  return t.charAt(0).toUpperCase() + t.slice(1);
}
