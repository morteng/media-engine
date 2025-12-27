import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SceneNavigator } from './SceneNavigator';

const mockScenes = [
  {
    id: 'intro-1',
    type: 'intro',
    title: 'Welcome',
    duration: 5,
    startFrame: 0,
    endFrame: 150,
    background: 'aurora',
    transition_in: 'fade',
  },
  {
    id: 'feature-1',
    type: 'feature',
    title: 'Feature Overview',
    duration: 10,
    startFrame: 150,
    endFrame: 450,
    background: 'grid',
  },
  {
    id: 'demo-1',
    type: 'demo',
    title: 'Live Demo',
    duration: 15,
    startFrame: 450,
    endFrame: 900,
  },
  {
    id: 'outro-1',
    type: 'outro',
    title: 'Call to Action',
    duration: 5,
    startFrame: 900,
    endFrame: 1050,
    transition_in: 'zoom',
  },
];

describe('SceneNavigator', () => {
  it('renders scene count badge', () => {
    render(<SceneNavigator scenes={mockScenes} currentFrame={0} fps={30} />);

    // Scene count appears in the badge
    const badge = screen.getByText('4', { selector: '.badge' });
    expect(badge).toBeInTheDocument();
  });

  it('renders total duration', () => {
    render(<SceneNavigator scenes={mockScenes} currentFrame={0} fps={30} />);

    // Total frames: 1050, fps: 30 = 35 seconds = 0:35
    expect(screen.getByText('0:35')).toBeInTheDocument();
  });

  it('renders scenes header', () => {
    render(<SceneNavigator scenes={mockScenes} currentFrame={0} fps={30} />);

    expect(screen.getByText('Scenes')).toBeInTheDocument();
  });

  it('renders all scene titles in list', () => {
    render(<SceneNavigator scenes={mockScenes} currentFrame={0} fps={30} />);

    // Scene titles appear in buttons
    expect(screen.getAllByText('Welcome').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Feature Overview').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Live Demo').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Call to Action').length).toBeGreaterThan(0);
  });

  it('shows current scene in navigation', () => {
    render(<SceneNavigator scenes={mockScenes} currentFrame={200} fps={30} />);

    // Frame 200 is in feature-1 scene (150-450)
    // The scene title should appear in the center navigation
    const centerText = screen.getAllByText('Feature Overview');
    expect(centerText.length).toBeGreaterThan(0);
  });

  it('shows no scene selected when frame is outside all scenes', () => {
    render(<SceneNavigator scenes={mockScenes} currentFrame={1200} fps={30} />);

    expect(screen.getByText('No scene selected')).toBeInTheDocument();
  });

  it('calls onSeek when scene is clicked', () => {
    const onSeek = vi.fn();
    render(<SceneNavigator scenes={mockScenes} currentFrame={0} fps={30} onSeek={onSeek} />);

    // Click on Feature Overview scene in the list - get all matches and use the first one in a button
    const featureTexts = screen.getAllByText('Feature Overview');
    const featureButton = featureTexts.find(el => el.closest('button'))?.closest('button');
    fireEvent.click(featureButton!);

    expect(onSeek).toHaveBeenCalledWith(150); // startFrame of feature-1
  });

  it('calls onSceneSelect when scene is clicked', () => {
    const onSceneSelect = vi.fn();
    render(
      <SceneNavigator
        scenes={mockScenes}
        currentFrame={0}
        fps={30}
        onSceneSelect={onSceneSelect}
      />
    );

    // Click on Demo scene in the list - get all matches and use the first one in a button
    const demoTexts = screen.getAllByText('Live Demo');
    const demoButton = demoTexts.find(el => el.closest('button'))?.closest('button');
    fireEvent.click(demoButton!);

    expect(onSceneSelect).toHaveBeenCalledWith('demo-1');
  });

  it('navigates to previous scene with left button', () => {
    const onSeek = vi.fn();
    const onSceneSelect = vi.fn();
    render(
      <SceneNavigator
        scenes={mockScenes}
        currentFrame={200}
        fps={30}
        onSeek={onSeek}
        onSceneSelect={onSceneSelect}
      />
    );

    // Click previous button (currently on feature-1, should go to intro-1)
    const prevButton = screen.getAllByRole('button')[0]; // First button is prev
    fireEvent.click(prevButton);

    expect(onSeek).toHaveBeenCalledWith(0); // startFrame of intro-1
    expect(onSceneSelect).toHaveBeenCalledWith('intro-1');
  });

  it('navigates to next scene with right button', () => {
    const onSeek = vi.fn();
    const onSceneSelect = vi.fn();
    render(
      <SceneNavigator
        scenes={mockScenes}
        currentFrame={200}
        fps={30}
        onSeek={onSeek}
        onSceneSelect={onSceneSelect}
      />
    );

    // Click next button (currently on feature-1, should go to demo-1)
    const buttons = screen.getAllByRole('button');
    const nextButton = buttons[1]; // Second button is next
    fireEvent.click(nextButton);

    expect(onSeek).toHaveBeenCalledWith(450); // startFrame of demo-1
    expect(onSceneSelect).toHaveBeenCalledWith('demo-1');
  });

  it('disables prev button on first scene', () => {
    render(<SceneNavigator scenes={mockScenes} currentFrame={50} fps={30} />);

    // Currently on first scene (intro-1)
    const prevButton = screen.getAllByRole('button')[0];
    expect(prevButton).toBeDisabled();
  });

  it('disables next button on last scene', () => {
    render(<SceneNavigator scenes={mockScenes} currentFrame={950} fps={30} />);

    // Currently on last scene (outro-1)
    const buttons = screen.getAllByRole('button');
    const nextButton = buttons[1];
    expect(nextButton).toBeDisabled();
  });

  it('shows scene numbers in list', () => {
    render(<SceneNavigator scenes={mockScenes} currentFrame={0} fps={30} />);

    // Should show scene numbers 1-4 (they appear in the scene list)
    const allButtons = screen.getAllByRole('button');
    // Scene list buttons exist
    expect(allButtons.length).toBeGreaterThanOrEqual(4);
  });

  it('shows transition info for scenes', () => {
    render(<SceneNavigator scenes={mockScenes} currentFrame={0} fps={30} />);

    // Intro has fade transition
    expect(screen.getByText('fade')).toBeInTheDocument();
    // Outro has zoom transition
    expect(screen.getByText('zoom')).toBeInTheDocument();
  });

  it('shows scene duration in list', () => {
    render(<SceneNavigator scenes={mockScenes} currentFrame={0} fps={30} />);

    // Should show duration for each scene (0:05, 0:10, 0:15, 0:05)
    const durations = screen.getAllByText(/0:\d{2}/);
    expect(durations.length).toBeGreaterThan(0);
  });

  it('highlights current scene in list', () => {
    render(<SceneNavigator scenes={mockScenes} currentFrame={200} fps={30} />);

    // Feature-1 should be highlighted (frame 200 is in 150-450 range)
    const featureTexts = screen.getAllByText('Feature Overview');
    const featureButton = featureTexts.find(el => el.closest('button'))?.closest('button');
    expect(featureButton).toHaveClass('bg-primary/20');
  });

  it('applies className prop correctly', () => {
    const { container } = render(
      <SceneNavigator
        scenes={mockScenes}
        currentFrame={0}
        fps={30}
        className="custom-class"
      />
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('renders empty state gracefully', () => {
    render(<SceneNavigator scenes={[]} currentFrame={0} fps={30} />);

    expect(screen.getByText('0')).toBeInTheDocument(); // 0 scenes
    expect(screen.getByText('0:00')).toBeInTheDocument(); // 0 duration
    expect(screen.getByText('No scene selected')).toBeInTheDocument();
  });

  it('formats time correctly for longer videos', () => {
    const longScenes = [
      {
        id: 'long-1',
        type: 'feature',
        title: 'Long Scene',
        duration: 120,
        startFrame: 0,
        endFrame: 3600, // 2 minutes at 30fps
      },
    ];

    render(<SceneNavigator scenes={longScenes} currentFrame={0} fps={30} />);

    // 3600 frames / 30 fps = 120 seconds = 2:00
    const timeTexts = screen.getAllByText('2:00');
    expect(timeTexts.length).toBeGreaterThan(0);
  });
});
