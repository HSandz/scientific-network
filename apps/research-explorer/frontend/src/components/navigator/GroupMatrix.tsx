import React from "react";
import { orgName, plural, subjectName } from "../../lib/names";
import { navigate, pathFor } from "../../lib/router";
import type { GroupsResponse } from "../../types/navigator";
import { Section } from "../ui/primitives";

const CAP = 3;

/**
 * Organization by topic specialisation. A single graphite scale (the thermal scale is kept for
 * momentum); each cell prints its value, so colour is never the only cue.
 */
export const GroupMatrix: React.FC<{ data: GroupsResponse; onSelectGroup: (id: string) => void }> = ({ data, onSelectGroup }) => {
  const m = data.matrix;
  const cell = new Map(m.cells.map((c) => [`${c.organization_name}|${c.subject_name}`, c]));
  const orgs = m.organizations
    .map((name) => ({ name, id: m.cells.find((c) => c.organization_name === name)?.organization_id }))
    .filter((o): o is { name: string; id: string } => Boolean(o.id));
  const topicId = new Map(m.cells.map((c) => [c.subject_name, c.subject_id]));

  return (
    <>
      <Section id="matrix" title="Who specialises in which topic" hint="The largest organizations in this selection against the 12 topics they publish on most. 1× is average.">
        {orgs.length ? (
          <>
            <div className="matrix-legend">
              <span>0×</span>
              <span className="matrix-scale" aria-hidden="true" />
              <span>{CAP}× or more</span>
              <span>A dash means no papers recorded.</span>
            </div>
            <div className="matrix-scroll" tabIndex={0} role="region" aria-label="Organization by topic table, scrolls sideways">
              <table className="matrix" data-chart-label="Organization by topic matrix" data-chart-rendered="true" data-chart-point-count={m.cells.length}>
                <thead>
                  <tr>
                    <th scope="col">Organization</th>
                    {m.topics.map((t) => (
                      <th key={t} scope="col">
                        <button type="button" onClick={() => topicId.get(t) && navigate(pathFor("topics", topicId.get(t)!))}>
                          {subjectName(t, "Topic")}
                        </button>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {orgs.map((o) => (
                    <tr key={o.id}>
                      <th scope="row">
                        <button type="button" onClick={() => onSelectGroup(o.id)}>
                          {orgName(o.name)}
                        </button>
                      </th>
                      {m.topics.map((t) => {
                        const c = cell.get(`${o.name}|${t}`);
                        if (!c) return <td key={t}>–</td>;
                        const k = Math.min(1, c.rca / CAP);
                        // Skip the mid greys, where neither text colour reaches 4.5:1.
                        const mix = k <= 0.66 ? k * 62 : 72 + (k - 0.66) * 38;
                        return (
                          <td
                            key={t}
                            className={k > 0.66 ? "dark" : ""}
                            style={{ background: `color-mix(in srgb, var(--ink) ${Math.round(mix)}%, var(--surface))` }}
                            title={`${orgName(o.name)}, ${subjectName(t, "Topic")}: ${c.rca.toFixed(2)}× average, ${plural(c.papers, "paper")}`}
                          >
                            {c.rca.toFixed(1)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <p className="note">No topic figures for this selection.</p>
        )}
      </Section>

      <div className="two-lists">
        <Section id="anchored" title="Co-author clusters led by one organization" hint="Clusters in the co-authorship network where one organization dominates. Clusters of 100 or more researchers are marked large.">
          <ul className="plain-list scroll-list">
            {data.org_anchored_communities.slice(0, 20).map((c) => (
              <li key={c.community}>
                <button type="button" className="rowlink" onClick={() => onSelectGroup(c.organization_id)}>
                  {c.display_name}
                </button>
                <span className="muted">
                  {plural(c.members, "researcher")}
                  {c.size_tier === "large" ? ", large" : ""}
                </span>
              </li>
            ))}
          </ul>
        </Section>
        <Section id="rollup" title="Parent organizations with their units" hint="Units are added to their parent organization. Government bodies are not used as parents.">
          <ul className="plain-list scroll-list">
            {data.rollup.slice(0, 20).map((r) => (
              <li key={r.parent}>
                <span className="rowtext">{orgName(r.parent_name)}</span>
                <span className="muted">
                  {plural(r.child_organizations, "unit")}, {plural(r.papers, "paper")}
                </span>
              </li>
            ))}
          </ul>
        </Section>
      </div>
    </>
  );
};
