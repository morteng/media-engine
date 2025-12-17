/**
 * Media Engine Remotion Components
 *
 * Motion graphics components for video production.
 */

import { registerRoot } from "remotion";
import { RemotionRoot } from "./Root";

// Register the root component for Remotion
registerRoot(RemotionRoot);

// Components
export { Background } from './components/Background';
export { TitleCard } from './components/TitleCard';
export { StatCounter, StatGrid } from './components/StatCounter';
export { FeatureCard, FeatureList } from './components/FeatureCard';
export { TextReveal, HighlightText, Typewriter, GradientText, CharacterReveal, AnimatedCounter } from './components/TextReveal';
export { Transition, Scene } from './components/Transition';
export type { TransitionType } from './components/Transition';
export { Overlay } from './components/Overlay';

// Theme and utilities
export { colors, typography, motion, gradients, glows, videoConfig, icons, particles, patterns } from './lib/theme';
export { ease, presets, animateCount, getStaggerDelay, revealText, revealWords } from './lib/animations';
