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
export { TextReveal, HighlightText, Typewriter } from './components/TextReveal';
export { Transition, Scene } from './components/Transition';
export { Overlay, DemoOverlay, StatOverlay, CalloutOverlay, LowerThirdOverlay } from './components/Overlay';

// Theme and utilities
export { colors, typography, motion, gradients, videoConfig, icons } from './lib/theme';
export { fadeIn, slideIn, scaleIn, springConfig, useAnimatedValue } from './lib/animations';
