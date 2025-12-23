import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { GraphLegend, knowledgeGraphLegend, dependencyGraphLegend, hierarchyGraphLegend } from './GraphLegend';

describe('GraphLegend', () => {
  it('renders legend items', () => {
    const items = [
      { label: 'Document', color: '#00d4ff' },
      { label: 'Concept', color: '#a855f7' },
    ];
    render(<GraphLegend items={items} />);

    expect(screen.getByText('Document')).toBeInTheDocument();
    expect(screen.getByText('Concept')).toBeInTheDocument();
  });

  it('renders empty when no items', () => {
    const { container } = render(<GraphLegend items={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('applies custom className', () => {
    const items = [{ label: 'Test', color: '#fff' }];
    const { container } = render(<GraphLegend items={items} className="custom-class" />);

    const legend = container.firstChild as HTMLElement;
    expect(legend).toHaveClass('custom-class');
  });

  it('renders color indicators with correct styles', () => {
    const items = [{ label: 'Primary', color: '#00d4ff' }];
    const { container } = render(<GraphLegend items={items} />);

    const colorIndicator = container.querySelector('[style*="background-color"]');
    expect(colorIndicator).toHaveStyle({ backgroundColor: '#00d4ff' });
  });
});

describe('Pre-defined legends', () => {
  it('knowledgeGraphLegend has expected items', () => {
    expect(knowledgeGraphLegend).toHaveLength(4);
    expect(knowledgeGraphLegend.map(i => i.label)).toContain('Document');
    expect(knowledgeGraphLegend.map(i => i.label)).toContain('Concept');
    expect(knowledgeGraphLegend.map(i => i.label)).toContain('Orphan');
    expect(knowledgeGraphLegend.map(i => i.label)).toContain('Hub');
  });

  it('dependencyGraphLegend has expected items', () => {
    expect(dependencyGraphLegend).toHaveLength(3);
    expect(dependencyGraphLegend.map(i => i.label)).toContain('Fresh');
    expect(dependencyGraphLegend.map(i => i.label)).toContain('Stale');
    expect(dependencyGraphLegend.map(i => i.label)).toContain('Dependencies');
  });

  it('hierarchyGraphLegend has expected items', () => {
    expect(hierarchyGraphLegend).toHaveLength(5);
    expect(hierarchyGraphLegend.map(i => i.label)).toContain('Chapter');
    expect(hierarchyGraphLegend.map(i => i.label)).toContain('Reference');
    expect(hierarchyGraphLegend.map(i => i.label)).toContain('Stale');
  });
});
