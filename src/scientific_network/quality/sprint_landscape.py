"""Reuse frozen topic analysis: show coverage beside labeled-paper topic shares."""
import argparse
import csv
import json
from pathlib import Path

from scientific_network.quality.sprint_audit import digest


def render(analysis: Path, output: Path) -> dict:
    if output.exists() or output.is_symlink():
        raise ValueError('use an unused output directory')
    source = json.loads(analysis.read_text())
    rows = source['release_metrics']['topic_shares_by_year_venue']['rows']
    grouped = {}
    for row in rows:
        key = row['venue_id'], row['year']
        counts = row['all_core_paper_count'], row['labeled_paper_count']
        if key in grouped and grouped[key] != counts:
            raise ValueError('inconsistent venue-year denominator')
        grouped[key] = counts
        if not 0 <= counts[1] <= counts[0] or counts[0] <= 0:
            raise ValueError('invalid coverage denominator')
    table = [{'venue': v.split(':')[-1].upper(), 'year': y, 'all_papers': a,
              'labeled_papers': b, 'unlabeled_papers': a-b, 'coverage': b/a}
             for (v,y), (a,b) in sorted(grouped.items())]
    output.mkdir(parents=True)
    with (output/'coverage.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(table[0])); writer.writeheader(); writer.writerows(table)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True, layout='constrained')
    for ax, venue in zip(axes, ['AAAI', 'IJCAI']):
        subset = [r for r in table if r['venue']==venue]
        ax.bar([r['year'] for r in subset], [100*r['coverage'] for r in subset], color='#315b87', label='Labeled')
        ax.bar([r['year'] for r in subset], [100*(1-r['coverage']) for r in subset], bottom=[100*r['coverage'] for r in subset], color='#dce2e9', label='Unlabeled')
        for r in subset:
            ax.text(r['year'], 45, f"{r['labeled_papers']:,}\n/ {r['all_papers']:,}", ha='center', va='center', color='white', fontsize=9)
        ax.set(title=venue, xlabel='Conference year', ylim=(0,100), xticks=[r['year'] for r in subset])
        ax.spines[['top','right']].set_visible(False)
    axes[0].set_ylabel('Share of all in-scope papers (%)'); axes[1].legend(loc='lower right')
    fig.savefig(output/'coverage.png', dpi=180); plt.close(fig)
    receipt = {'graph_version': source['graph_version'], 'analysis_path': str(analysis),
               'analysis_sha256': digest(analysis), 'method': 'reuse frozen venue-year denominators; no classifier run',
               'all_papers': sum(r['all_papers'] for r in table), 'labeled_papers': sum(r['labeled_papers'] for r in table),
               'artifact_sha256': {p.name:digest(p) for p in output.iterdir()}}
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--analysis',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(render(a.analysis,a.output),indent=2))


if __name__=='__main__': main()
