import { useState } from 'react';
import { Layers, Sparkles, ArrowRight, Type, Layout } from 'lucide-react';

type ComponentCategory = 'background' | 'text' | 'transition' | 'layout' | 'effect';

interface MotionComponent {
  id: string;
  name: string;
  category: ComponentCategory;
  description: string;
  energy: 'low' | 'medium' | 'high';
  props: ComponentProp[];
  useFor: string[];
  avoidFor?: string[];
  preview?: string;
}

interface ComponentProp {
  name: string;
  type: string;
  default?: string;
  description: string;
}

// Component catalog based on video_design_knowledge.py
const COMPONENTS: MotionComponent[] = [
  // Backgrounds
  {
    id: 'dark',
    name: 'Dark Background',
    category: 'background',
    description: 'Professional dark background for high contrast content',
    energy: 'low',
    props: [
      { name: 'opacity', type: 'number', default: '1', description: 'Background opacity' },
      { name: 'gradient', type: 'boolean', default: 'false', description: 'Enable subtle gradient' },
    ],
    useFor: ['demos', 'text-heavy scenes', 'focus content'],
  },
  {
    id: 'aurora',
    name: 'Aurora Background',
    category: 'background',
    description: 'Dynamic aurora borealis animation with brand colors',
    energy: 'medium',
    props: [
      { name: 'speed', type: 'number', default: '1', description: 'Animation speed multiplier' },
      { name: 'intensity', type: 'number', default: '0.8', description: 'Color intensity' },
    ],
    useFor: ['intros', 'outros', 'brand moments'],
  },
  {
    id: 'grid',
    name: 'Grid Background',
    category: 'background',
    description: 'Technical grid pattern for structured content',
    energy: 'low',
    props: [
      { name: 'spacing', type: 'number', default: '40', description: 'Grid line spacing in pixels' },
      { name: 'animated', type: 'boolean', default: 'false', description: 'Enable pulse animation' },
    ],
    useFor: ['features', 'data', 'structured content'],
  },
  {
    id: 'particles',
    name: 'Particles Background',
    category: 'background',
    description: 'Floating particles for dynamic energy',
    energy: 'medium',
    props: [
      { name: 'count', type: 'number', default: '50', description: 'Number of particles' },
      { name: 'speed', type: 'number', default: '1', description: 'Movement speed' },
    ],
    useFor: ['intros', 'highlights', 'transitions'],
  },
  {
    id: 'cyber',
    name: 'Cyber Background',
    category: 'background',
    description: 'Futuristic cyber theme with tech elements',
    energy: 'high',
    props: [
      { name: 'glitchEnabled', type: 'boolean', default: 'true', description: 'Enable glitch effects' },
    ],
    useFor: ['tech content', 'innovation themes'],
  },
  // Text Effects
  {
    id: 'fade-up',
    name: 'Fade Up',
    category: 'text',
    description: 'Text fades in while moving upward',
    energy: 'low',
    props: [
      { name: 'duration', type: 'number', default: '0.5', description: 'Animation duration in seconds' },
      { name: 'delay', type: 'number', default: '0', description: 'Start delay in seconds' },
    ],
    useFor: ['any text', 'professional content'],
  },
  {
    id: 'bounce',
    name: 'Bounce',
    category: 'text',
    description: 'Text bounces in with elastic effect',
    energy: 'high',
    props: [
      { name: 'stiffness', type: 'number', default: '200', description: 'Spring stiffness' },
      { name: 'damping', type: 'number', default: '10', description: 'Spring damping' },
    ],
    useFor: ['intros', 'emphasis', 'playful brands'],
  },
  {
    id: 'wave',
    name: 'Wave',
    category: 'text',
    description: 'Characters animate in a wave pattern',
    energy: 'medium',
    props: [
      { name: 'stagger', type: 'number', default: '0.05', description: 'Delay between characters' },
    ],
    useFor: ['lists', 'multi-word reveals'],
  },
  {
    id: 'scale-pop',
    name: 'Scale Pop',
    category: 'text',
    description: 'Text pops in with scale animation',
    energy: 'high',
    props: [
      { name: 'scale', type: 'number', default: '1.2', description: 'Initial scale' },
    ],
    useFor: ['numbers', 'stats', 'emphasis'],
  },
  {
    id: 'glitch-text',
    name: 'Glitch Text',
    category: 'text',
    description: 'Digital glitch effect on text',
    energy: 'high',
    props: [
      { name: 'intensity', type: 'number', default: '0.5', description: 'Glitch intensity' },
    ],
    useFor: ['tech content', 'brief emphasis'],
    avoidFor: ['long text', 'readability-critical'],
  },
  // Transitions
  {
    id: 'fade',
    name: 'Fade',
    category: 'transition',
    description: 'Simple crossfade between scenes',
    energy: 'low',
    props: [
      { name: 'duration', type: 'number', default: '0.5', description: 'Transition duration' },
    ],
    useFor: ['any scene change', 'calm transitions'],
    avoidFor: ['high-energy sequences'],
  },
  {
    id: 'wipe',
    name: 'Wipe',
    category: 'transition',
    description: 'Directional wipe transition',
    energy: 'medium',
    props: [
      { name: 'direction', type: 'string', default: 'left', description: 'Wipe direction' },
    ],
    useFor: ['directional flow', 'progression'],
  },
  {
    id: 'glitch',
    name: 'Glitch',
    category: 'transition',
    description: 'Digital glitch transition effect',
    energy: 'high',
    props: [
      { name: 'intensity', type: 'number', default: '0.8', description: 'Glitch intensity' },
    ],
    useFor: ['tech content', 'intros', 'emphasis'],
    avoidFor: ['calm sections', 'conservative brands'],
  },
  {
    id: 'slice',
    name: 'Slice',
    category: 'transition',
    description: 'Scene splits and reveals next',
    energy: 'high',
    props: [
      { name: 'slices', type: 'number', default: '5', description: 'Number of slices' },
    ],
    useFor: ['dynamic reveals', 'feature highlights'],
  },
  {
    id: 'zoom-burst',
    name: 'Zoom Burst',
    category: 'transition',
    description: 'Explosive zoom transition',
    energy: 'high',
    props: [
      { name: 'scale', type: 'number', default: '2', description: 'Zoom scale' },
    ],
    useFor: ['emphasis', 'reveals', 'intros'],
    avoidFor: ['frequent use', 'calm content'],
  },
  // Layouts
  {
    id: 'split-screen',
    name: 'Split Screen',
    category: 'layout',
    description: 'Side-by-side content layout',
    energy: 'medium',
    props: [
      { name: 'ratio', type: 'string', default: '50-50', description: 'Split ratio' },
      { name: 'angle', type: 'number', default: '15', description: 'Divider angle in degrees' },
    ],
    useFor: ['comparisons', 'demo + text'],
  },
  {
    id: 'centered',
    name: 'Centered',
    category: 'layout',
    description: 'Content centered on screen',
    energy: 'low',
    props: [
      { name: 'maxWidth', type: 'number', default: '80', description: 'Max width percentage' },
    ],
    useFor: ['titles', 'quotes', 'CTAs'],
  },
  {
    id: 'grid-layout',
    name: 'Grid Layout',
    category: 'layout',
    description: 'Content arranged in grid',
    energy: 'low',
    props: [
      { name: 'columns', type: 'number', default: '3', description: 'Number of columns' },
      { name: 'gap', type: 'number', default: '20', description: 'Gap between items' },
    ],
    useFor: ['features list', 'icons', 'multiple items'],
  },
];

const CATEGORY_ICONS: Record<ComponentCategory, React.ReactNode> = {
  background: <Layers className="h-4 w-4" />,
  text: <Type className="h-4 w-4" />,
  transition: <ArrowRight className="h-4 w-4" />,
  layout: <Layout className="h-4 w-4" />,
  effect: <Sparkles className="h-4 w-4" />,
};

const ENERGY_COLORS: Record<string, string> = {
  low: 'badge-success',
  medium: 'badge-warning',
  high: 'badge-error',
};

interface ComponentLibraryProps {
  onSelectComponent?: (component: MotionComponent) => void;
  className?: string;
}

export function ComponentLibrary({ onSelectComponent, className = '' }: ComponentLibraryProps) {
  const [selectedCategory, setSelectedCategory] = useState<ComponentCategory | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedComponent, setSelectedComponent] = useState<MotionComponent | null>(null);

  const categories: (ComponentCategory | 'all')[] = ['all', 'background', 'text', 'transition', 'layout'];

  const filteredComponents = COMPONENTS.filter((comp) => {
    const matchesCategory = selectedCategory === 'all' || comp.category === selectedCategory;
    const matchesSearch =
      searchQuery === '' ||
      comp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      comp.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const handleSelectComponent = (component: MotionComponent) => {
    setSelectedComponent(component);
    onSelectComponent?.(component);
  };

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Search and filters */}
      <div className="p-4 border-b border-base-300 space-y-3">
        <input
          type="text"
          placeholder="Search components..."
          className="input input-bordered input-sm w-full"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />

        <div className="flex gap-1 flex-wrap">
          {categories.map((cat) => (
            <button
              key={cat}
              className={`btn btn-xs ${selectedCategory === cat ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat === 'all' ? 'All' : (
                <span className="flex items-center gap-1">
                  {CATEGORY_ICONS[cat]}
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Component list */}
      <div className="flex-1 overflow-auto">
        <div className="grid grid-cols-1 gap-2 p-4">
          {filteredComponents.map((component) => (
            <div
              key={component.id}
              className={`card card-compact bg-base-200 cursor-pointer hover:bg-base-300 transition-colors ${
                selectedComponent?.id === component.id ? 'ring-2 ring-primary' : ''
              }`}
              onClick={() => handleSelectComponent(component)}
            >
              <div className="card-body">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-base-content/60">
                      {CATEGORY_ICONS[component.category]}
                    </span>
                    <h3 className="font-medium">{component.name}</h3>
                  </div>
                  <span className={`badge badge-xs ${ENERGY_COLORS[component.energy]}`}>
                    {component.energy}
                  </span>
                </div>
                <p className="text-xs text-base-content/70">{component.description}</p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {component.useFor.slice(0, 3).map((use) => (
                    <span key={use} className="badge badge-xs badge-ghost">
                      {use}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Component details panel */}
      {selectedComponent && (
        <div className="border-t border-base-300 p-4 bg-base-200">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-bold">{selectedComponent.name}</h3>
            <button
              className="btn btn-ghost btn-xs"
              onClick={() => setSelectedComponent(null)}
            >
              ✕
            </button>
          </div>

          <p className="text-sm text-base-content/70 mb-3">{selectedComponent.description}</p>

          {/* Props */}
          <div className="mb-3">
            <h4 className="text-xs font-semibold mb-1 text-base-content/60">PROPS</h4>
            <div className="space-y-1">
              {selectedComponent.props.map((prop) => (
                <div key={prop.name} className="flex items-center gap-2 text-xs">
                  <code className="bg-base-300 px-1 rounded">{prop.name}</code>
                  <span className="text-base-content/50">{prop.type}</span>
                  {prop.default && (
                    <span className="text-primary">= {prop.default}</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Use for */}
          <div className="mb-2">
            <h4 className="text-xs font-semibold mb-1 text-base-content/60">BEST FOR</h4>
            <div className="flex flex-wrap gap-1">
              {selectedComponent.useFor.map((use) => (
                <span key={use} className="badge badge-xs badge-success badge-outline">
                  {use}
                </span>
              ))}
            </div>
          </div>

          {/* Avoid for */}
          {selectedComponent.avoidFor && (
            <div>
              <h4 className="text-xs font-semibold mb-1 text-base-content/60">AVOID FOR</h4>
              <div className="flex flex-wrap gap-1">
                {selectedComponent.avoidFor.map((avoid) => (
                  <span key={avoid} className="badge badge-xs badge-error badge-outline">
                    {avoid}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
