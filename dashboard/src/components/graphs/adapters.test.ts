import { describe, it, expect } from 'vitest';
import {
  toReagraphNodesFromKnowledgeGraph,
  toReagraphEdgesFromKnowledgeGraph,
  toReagraphNodesFromFlowGraph,
  toReagraphEdgesFromFlowGraph,
  toReagraphNodesFromOrphans,
  toReagraphFormat,
} from './adapters';
import type { GraphNode, GraphLink, FlowGraphNode, FlowGraphEdge } from '@/api/types';

describe('toReagraphNodesFromKnowledgeGraph', () => {
  const mockNodes: GraphNode[] = [
    {
      id: 'node1',
      title: 'Introduction',
      document: 'intro.md',
      type: 'chapter',
      status: 'published',
      language: 'en',
      word_count: 1000,
    },
    {
      id: 'node2',
      title: 'API Reference',
      document: 'api.md',
      type: 'concept',
      status: 'draft',
      language: 'en',
      word_count: 500,
    },
  ];

  it('converts nodes to Reagraph format', () => {
    const result = toReagraphNodesFromKnowledgeGraph(mockNodes, true);

    expect(result).toHaveLength(2);
    expect(result[0].id).toBe('node1');
    expect(result[0].label).toBe('Introduction');
    expect(result[1].id).toBe('node2');
    expect(result[1].label).toBe('API Reference');
  });

  it('includes data properties', () => {
    const result = toReagraphNodesFromKnowledgeGraph(mockNodes, true);

    expect(result[0].data).toMatchObject({
      document: 'intro.md',
      type: 'chapter',
      status: 'published',
    });
  });

  it('calculates size based on word count', () => {
    const result = toReagraphNodesFromKnowledgeGraph(mockNodes, true);

    // node1 has 1000 words, node2 has 500 - node1 should be larger
    expect(result[0].size).toBeGreaterThan(result[1].size!);
  });

  it('applies colors based on dark mode', () => {
    const darkResult = toReagraphNodesFromKnowledgeGraph(mockNodes, true);
    const lightResult = toReagraphNodesFromKnowledgeGraph(mockNodes, false);

    // Colors should be different between dark and light mode
    expect(darkResult[0].fill).toBeDefined();
    expect(lightResult[0].fill).toBeDefined();
  });
});

describe('toReagraphEdgesFromKnowledgeGraph', () => {
  const mockEdges: GraphLink[] = [
    { source: 'node1', target: 'node2', type: 'references', weight: 1 },
    { source: 'node2', target: 'node3', type: 'implements', weight: 2 },
  ];

  it('converts edges to Reagraph format', () => {
    const result = toReagraphEdgesFromKnowledgeGraph(mockEdges);

    expect(result).toHaveLength(2);
    expect(result[0].source).toBe('node1');
    expect(result[0].target).toBe('node2');
    expect(result[0].label).toBe('references');
  });

  it('generates unique edge IDs', () => {
    const result = toReagraphEdgesFromKnowledgeGraph(mockEdges);

    expect(result[0].id).toBe('edge-node1-node2-0');
    expect(result[1].id).toBe('edge-node2-node3-1');
  });

  it('calculates size based on weight', () => {
    const result = toReagraphEdgesFromKnowledgeGraph(mockEdges);

    expect(result[1].size).toBeGreaterThan(result[0].size!);
  });
});

describe('toReagraphNodesFromFlowGraph', () => {
  const mockNodes: FlowGraphNode[] = [
    {
      id: 'flow1',
      title: 'Chapter 1',
      doc_type: 'chapter',
      lifecycle: 'published',
      is_stale: false,
      level: 1,
      sequence_order: 1,
      position: { x: 0, y: 0 },
    },
    {
      id: 'flow2',
      title: 'Script 1',
      doc_type: 'script',
      lifecycle: 'draft',
      is_stale: true,
      level: 2,
      sequence_order: 1,
      position: { x: 100, y: 100 },
    },
  ];

  it('converts flow graph nodes', () => {
    const result = toReagraphNodesFromFlowGraph(mockNodes, true);

    expect(result).toHaveLength(2);
    expect(result[0].id).toBe('flow1');
    expect(result[0].label).toBe('Chapter 1');
    expect(result[1].id).toBe('flow2');
  });

  it('includes staleness in data', () => {
    const result = toReagraphNodesFromFlowGraph(mockNodes, true);

    expect(result[0].data?.isStale).toBe(false);
    expect(result[1].data?.isStale).toBe(true);
  });
});

describe('toReagraphEdgesFromFlowGraph', () => {
  const mockEdges: FlowGraphEdge[] = [
    { source: 'flow1', target: 'flow2', type: 'parent', is_stale: false, version: null },
    { source: 'flow2', target: 'flow3', type: 'derives_from', is_stale: true, version: '1.0' },
  ];

  it('converts flow graph edges', () => {
    const result = toReagraphEdgesFromFlowGraph(mockEdges);

    expect(result).toHaveLength(2);
    expect(result[0].source).toBe('flow1');
    expect(result[0].target).toBe('flow2');
    expect(result[0].label).toBe('parent');
  });

  it('marks stale edges with larger size', () => {
    const result = toReagraphEdgesFromFlowGraph(mockEdges);

    expect(result[1].size).toBeGreaterThan(result[0].size!);
  });
});

describe('toReagraphNodesFromOrphans', () => {
  it('converts string orphans', () => {
    const orphans = ['Authentication', 'Authorization', 'API'];
    const result = toReagraphNodesFromOrphans(orphans, true);

    expect(result).toHaveLength(3);
    expect(result[0].label).toBe('Authentication');
    expect(result[0].data?.type).toBe('orphan');
  });

  it('converts object orphans with mention count', () => {
    const orphans = [
      { concept: 'Token', mention_count: 10 },
      { concept: 'Session', mention_count: 2 },
    ];
    const result = toReagraphNodesFromOrphans(orphans, true);

    expect(result).toHaveLength(2);
    expect(result[0].label).toBe('Token');
    expect(result[0].data?.mentionCount).toBe(10);
    // Higher mention count should result in larger size
    expect(result[0].size).toBeGreaterThan(result[1].size!);
  });
});

describe('toReagraphFormat', () => {
  it('handles empty data', () => {
    const result = toReagraphFormat({}, true);

    expect(result.nodes).toHaveLength(0);
    expect(result.edges).toHaveLength(0);
  });

  it('auto-detects and converts generic node format', () => {
    const data = {
      nodes: [
        { id: 'a', title: 'Node A', type: 'chapter' },
        { id: 'b', title: 'Node B', doc_type: 'script' },
      ],
      edges: [{ source: 'a', target: 'b', type: 'parent' }],
    };
    const result = toReagraphFormat(data, true);

    expect(result.nodes).toHaveLength(2);
    expect(result.nodes[0].label).toBe('Node A');
    expect(result.edges).toHaveLength(1);
  });

  it('handles links array instead of edges', () => {
    const data = {
      nodes: [{ id: 'a' }],
      links: [{ source: 'a', target: 'b' }],
    };
    const result = toReagraphFormat(data, true);

    expect(result.edges).toHaveLength(1);
    expect(result.edges[0].source).toBe('a');
  });

  it('generates IDs when missing', () => {
    const data = {
      nodes: [{ title: 'No ID Node' }],
      edges: [],
    };
    const result = toReagraphFormat(data, true);

    expect(result.nodes[0].id).toBe('node-0');
  });
});
