/**
 * useDemoToRemotionProps - Transform demo recording data to Remotion player props
 *
 * Converts the YAML-based demo structure to the props needed by
 * the RemotionPlayerWrapper component.
 *
 * Supports two modes:
 * 1. Pre-computed keyframes from API (preferred) - uses resolved CSS selectors
 * 2. Fallback presets (zoom_in, pan_left, etc.) - simple animations
 */

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { DemoRecordingDetail, DemoRecordingState } from '@/api/video';
import { getDemoStateCameraData } from '@/api/video';
import type { RemotionDemoProps, CameraKeyframe } from '@/components/remotion-preview/types';
import { defaultEffectsConfig } from '@/lib/effects';

const DEFAULT_FPS = 30;
const DEFAULT_VIEWPORT_WIDTH = 1920;
const DEFAULT_VIEWPORT_HEIGHT = 1080;
const DEFAULT_BACKGROUND = '#1a1a2e';

interface UseDemoToRemotionPropsResult {
  props: RemotionDemoProps | null;
  screenshotUrl: string | null;
  hasScreenshot: boolean;
  totalFrames: number;
  fps: number;
  hasCameraData: boolean;
  isLoadingCameraData: boolean;
}

/**
 * Transform a demo state's camera configuration to keyframes (fallback)
 */
function transformCameraToKeyframes(
  state: DemoRecordingState,
  fps: number,
  viewportWidth: number,
  viewportHeight: number
): CameraKeyframe[] {
  // If the state has explicit keyframes, use them
  if (state.camera?.keyframes && state.camera.keyframes.length > 0) {
    return state.camera.keyframes;
  }

  // Calculate center of viewport for default position
  const centerX = viewportWidth / 2;
  const centerY = viewportHeight / 2;

  // Duration in frames
  const durationSecs = state.duration || 2;
  const durationFrames = Math.floor(durationSecs * fps);

  // If there's a camera preset, generate keyframes based on it
  const preset = state.camera?.preset || 'static';

  switch (preset) {
    case 'zoom_in':
      return [
        { frame: 0, centerX, centerY, zoom: 1.0, easing: 'easeInOutCubic' },
        { frame: durationFrames, centerX, centerY, zoom: 1.5 },
      ];

    case 'zoom_out':
      return [
        { frame: 0, centerX, centerY, zoom: 1.5, easing: 'easeInOutCubic' },
        { frame: durationFrames, centerX, centerY, zoom: 1.0 },
      ];

    case 'pan_left':
      return [
        { frame: 0, centerX: centerX + 200, centerY, zoom: 1.2, easing: 'easeInOutCubic' },
        { frame: durationFrames, centerX: centerX - 200, centerY, zoom: 1.2 },
      ];

    case 'pan_right':
      return [
        { frame: 0, centerX: centerX - 200, centerY, zoom: 1.2, easing: 'easeInOutCubic' },
        { frame: durationFrames, centerX: centerX + 200, centerY, zoom: 1.2 },
      ];

    case 'drift':
      return [
        { frame: 0, centerX, centerY, zoom: 1.0, easing: 'easeInOutSine' },
        { frame: Math.floor(durationFrames / 2), centerX: centerX + 50, centerY: centerY + 30, zoom: 1.05 },
        { frame: durationFrames, centerX, centerY, zoom: 1.0 },
      ];

    case 'reveal':
      return [
        { frame: 0, centerX, centerY, zoom: 2.0, easing: 'easeOutExpo' },
        { frame: durationFrames, centerX, centerY, zoom: 1.0 },
      ];

    case 'static':
    default:
      // Single keyframe at default position
      return [{ frame: 0, centerX, centerY, zoom: 1.0 }];
  }
}

/**
 * Hook to fetch pre-computed camera data for a demo state
 */
export function useDemoStateCameraData(
  demoId: string | null,
  stateId: string | null,
  language = 'en'
) {
  return useQuery({
    queryKey: ['demoStateCameraData', demoId, stateId, language],
    queryFn: () => getDemoStateCameraData(demoId!, stateId!, language),
    enabled: !!demoId && !!stateId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false, // Don't retry if no camera data exists
  });
}

/**
 * Hook to transform demo data to Remotion props
 *
 * Automatically fetches pre-computed camera data when available.
 * Falls back to simple preset-based keyframes if no camera data exists.
 */
export function useDemoToRemotionProps(
  demoDetail: DemoRecordingDetail | null | undefined,
  selectedStateId: string | null
): UseDemoToRemotionPropsResult {
  // Fetch pre-computed camera data
  const {
    data: cameraData,
    isLoading: isLoadingCameraData,
  } = useDemoStateCameraData(
    demoDetail?.id ?? null,
    selectedStateId,
    'en'
  );

  return useMemo(() => {
    if (!demoDetail) {
      return {
        props: null,
        screenshotUrl: null,
        hasScreenshot: false,
        totalFrames: 0,
        fps: DEFAULT_FPS,
        hasCameraData: false,
        isLoadingCameraData: false,
      };
    }

    // Get viewport dimensions
    const viewportWidth = demoDetail.viewport?.width || DEFAULT_VIEWPORT_WIDTH;
    const viewportHeight = demoDetail.viewport?.height || DEFAULT_VIEWPORT_HEIGHT;
    const fps = DEFAULT_FPS;

    // Find the selected state
    const state = selectedStateId
      ? demoDetail.states.find((s) => s.id === selectedStateId)
      : demoDetail.states[0];

    if (!state) {
      return {
        props: null,
        screenshotUrl: null,
        hasScreenshot: false,
        totalFrames: 0,
        fps,
        hasCameraData: false,
        isLoadingCameraData,
      };
    }

    // Calculate duration and frames
    const durationSecs = state.duration || 2;
    const totalFrames = Math.floor(durationSecs * fps);

    // Use pre-computed keyframes if available, otherwise use fallback
    const hasCameraData = !!cameraData?.has_data && (cameraData?.keyframes?.length ?? 0) > 0;
    let keyframes: CameraKeyframe[];
    let background = DEFAULT_BACKGROUND;
    let shadow = true;
    let captureWidth = viewportWidth;
    let captureHeight = viewportHeight;
    let effects = defaultEffectsConfig;

    if (hasCameraData && cameraData) {
      // Use pre-computed camera data
      keyframes = cameraData.keyframes!;
      background = cameraData.background || DEFAULT_BACKGROUND;
      shadow = cameraData.shadow ?? true;

      // If capture_scale is set, use scaled dimensions
      if (cameraData.capture_scale && cameraData.capture_scale > 1) {
        captureWidth = viewportWidth * cameraData.capture_scale;
        captureHeight = viewportHeight * cameraData.capture_scale;
      }

      // Use effects from camera data if available
      if (cameraData.effects) {
        effects = {
          ...defaultEffectsConfig,
          ...cameraData.effects,
        };
      }
    } else {
      // Fallback to preset-based keyframes
      keyframes = transformCameraToKeyframes(state, fps, viewportWidth, viewportHeight);
    }

    // Build screenshot URL
    const screenshotUrl = state.has_actions || state.has_setup
      ? `/demos/${demoDetail.id}/states/${state.id}.png`
      : null;

    const props: RemotionDemoProps = {
      screenshotUrl: screenshotUrl || '',
      captureWidth,
      captureHeight,
      keyframes,
      background,
      shadow,
      effects,
      totalFrames,
      fps,
    };

    return {
      props,
      screenshotUrl,
      hasScreenshot: !!screenshotUrl,
      totalFrames,
      fps,
      hasCameraData,
      isLoadingCameraData,
    };
  }, [demoDetail, selectedStateId, cameraData, isLoadingCameraData]);
}

export default useDemoToRemotionProps;
