import { useQuery } from "@tanstack/react-query";
import { navigatorApi, type PaperMeta } from "./navigatorApi";

/** Titles, venues and authors for a set of paper ids (batched, cached). */
export function usePapers(ids: string[]) {
  const unique = [...new Set(ids.filter((x) => typeof x === "string" && x.startsWith("paper:")))].sort();
  return useQuery({
    queryKey: ["papers", unique],
    enabled: unique.length > 0,
    staleTime: 3_600_000,
    queryFn: async ({ signal }) => {
      const out: Record<string, PaperMeta> = {};
      for (let i = 0; i < unique.length; i += 60) {
        const res = await navigatorApi.getPapers(unique.slice(i, i + 60), signal);
        Object.assign(out, res.papers);
      }
      return out;
    },
  });
}

export function paperMeta(p: PaperMeta | undefined): string {
  if (!p) return "";
  const authors = p.authors.length ? `${p.authors.join(", ")}${p.n_authors > p.authors.length ? " and others" : ""}` : "";
  return [p.venue && p.year ? `${p.venue} ${p.year}` : p.venue || p.year || "", authors].filter(Boolean).join(", ");
}
